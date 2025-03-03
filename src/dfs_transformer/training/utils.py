#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 10:54:35 2021

@author: chrisw
"""

import torch
import torch.nn as nn
import numpy as np
import dfs_code
from chemprop.features.featurization import atom_features, bond_features
from copy import deepcopy
from collections import defaultdict
from einops import rearrange
from ..utils import FeaturizedDFSCodes2Dict

def to_cuda(T, device):
    if type(T) is dict:
        return {key: value.to(device) for key, value in T.items()}
    elif type(T) is list:
        return [t.to(device) for t in T]
    else:
        return T.to(device)


def dict_loss(pred, target, ce=nn.CrossEntropyLoss(ignore_index=-1)):
    """
    
    Parameters
    ----------
    pred : dict of predicted sequences
    target : dict of target sequences
    ce : torch loss function, optional
        DESCRIPTION. The default is nn.CrossEntropyLoss(ignore_index=-1).

    Returns
    -------
    loss over all sequences.
    """
    loss = 0.
    for key, seq in pred.items():
        tgt = target[key]
        loss += ce(rearrange(seq, 'd0 d1 d2 -> (d0 d1) d2'),
                   rearrange(tgt, 'd0 d1 -> (d0 d1)'))
    return loss


def dict_acc(pred, target, key):
    with torch.no_grad():
        tgt = rearrange(target[key], 'd0 d1 -> (d0 d1)')
        prd = rearrange(pred[key], 'd0 d1 d2 -> (d0 d1) d2')
        mask = tgt != -1
        n_tgts = torch.sum(mask)
        acc = (torch.argmax(prd[mask], axis=1) == tgt[mask]).sum()/n_tgts
        return acc
    
        
def seq_loss(pred, target, m, ce=nn.CrossEntropyLoss(ignore_index=-1)):
    """
    
    Parameters
    ----------
    pred : prediction sequence [seq_len, batch, 5*emb_dim]
    target : target sequence [seq_len, batch, 5] (or 8 instead of 5 cause of the indices)
    m : model config
    ce : loss to apply for each component. The default is nn.CrossEntropyLoss(ignore_index=-1).

    Returns
    -------
    loss : loss for the batch

    """
    dfs1, dfs2, atm1, atm2, bnd = pred
    pred_dfs1 = torch.reshape(dfs1, (-1, m.max_nodes))
    pred_dfs2 = torch.reshape(dfs2, (-1, m.max_nodes))
    pred_atm1 = torch.reshape(atm1, (-1, m.n_atoms))
    pred_atm2 = torch.reshape(atm2, (-1, m.n_atoms))
    pred_bnd = torch.reshape(bnd, (-1, m.n_bonds))
    tgt_dfs1 = target[:, :, 0].view(-1)
    tgt_dfs2 = target[:, :, 1].view(-1)
    tgt_atm1 = target[:, :, 2].view(-1)
    tgt_atm2 = target[:, :, 4].view(-1)
    tgt_bnd = target[:, :, 3].view(-1)
    loss = ce(pred_dfs1, tgt_dfs1) 
    loss += ce(pred_dfs2, tgt_dfs2)
    loss += ce(pred_atm1, tgt_atm1)
    loss += ce(pred_bnd, tgt_bnd)
    loss += ce(pred_atm2, tgt_atm2)
    return loss 

def seq_acc(pred, target, idx=0):
    with torch.no_grad():
        tgt_idx = {0:0, 1:1, 2:2, 3:4, 4:3}
        tgt = target[:, :, tgt_idx[idx]].view(-1)
        prd = pred[idx].reshape(tgt.shape[0], -1)
        mask = tgt != -1
        n_tgts = torch.sum(mask)
        acc = (torch.argmax(prd[mask], axis=1) == tgt[mask]).sum()/n_tgts
        return acc

def dfs_codes_to_dicts(code_batch, nfeat_batch, efeat_batch, masks=None, padding_value=-1000, missing_value=-1): 
    dfs_codes = defaultdict(list)
    if masks is not None:
        for mask, inp, nfeats, efeats in zip(masks, code_batch, nfeat_batch, efeat_batch):
            dfs_codes['dfs_from'] += [inp[:, 0]]
            dfs_codes['dfs_to'] += [inp[:, 1]]
            
            atm_from_feats = torch.ones((inp.shape[0], nfeats.shape[1]))
            atm_from_feats[mask] *= nfeats[inp[mask][:, -3]]
            atm_from_feats[~mask] *= missing_value
            
            atm_to_feats = torch.ones((inp.shape[0], nfeats.shape[1]))
            atm_to_feats[mask] *= nfeats[inp[mask][:, -1]]
            atm_to_feats[~mask] *= missing_value
            
            bnd_feats = torch.ones((inp.shape[0], efeats.shape[1]))
            bnd_feats[mask] *= efeats[inp[mask][:, -2]]
            bnd_feats[~mask] *= missing_value
            
            dfs_codes['atm_from'] += [atm_from_feats]
            dfs_codes['atm_to'] += [atm_to_feats]
            dfs_codes['bnd'] += [bnd_feats]   
    else:
        for inp, nfeats, efeats in zip(code_batch, nfeat_batch, efeat_batch):
            dfs_codes['dfs_from'] += [inp[:, 0]]
            dfs_codes['dfs_to'] += [inp[:, 1]]
            atm_from_feats = nfeats[inp[:, -3]]
            atm_to_feats = nfeats[inp[:, -1]]
            bnd_feats = efeats[inp[:, -2]]
            dfs_codes['atm_from'] += [atm_from_feats]
            dfs_codes['atm_to'] += [atm_to_feats]
            dfs_codes['bnd'] += [bnd_feats]
            
    dfs_codes = {key: nn.utils.rnn.pad_sequence(values, padding_value=padding_value).clone()
                 for key, values in dfs_codes.items()}
    return dfs_codes


def BERTizeLegacy(codes, fraction_missing=0.15, fraction_mask=0.8, fraction_rand=0.1):
    """
    Training the language model in BERT is done by predicting 15% of the tokens in the input, that were randomly picked. 
    These tokens are pre-processed as follows — 80% are replaced with a “[MASK]” token, 10% with a random word, and 10% 
    use the original word. 
    
    to get a random word we use the following strategy: we copy an random entry to that position 
    TODO: in the future one could also in addition implement a flip of the edge direction with a 50% chance
    
    returns preprocessed input sequences, target sequences and a mask indicating which inputs are part of the 15% masked, orig, rnd
    """
    fraction_orig = 1. - fraction_mask - fraction_rand
    fo = fraction_orig
    fm = fraction_mask
    fr = fraction_rand
    inputs = []
    targets = []
    masks_input = []
    masks_target = []
    for code in codes:
        n = len(code)
        perm = np.random.permutation(n)
        perm2 = np.random.permutation(n)
        mask_input = torch.zeros(n, dtype=bool)
        mask_input[perm[:int(fraction_missing*fm*n)]] = True
        mask_input = ~mask_input
        mask_target = torch.zeros(n, dtype=bool)
        mask_target[perm[int(fraction_missing*n):]] = True
        mask_target = ~mask_target
        delete_target_idx = perm[int(fraction_missing*n):]
        delete_input_idx = perm[:int(fraction_missing*fm*n)]
        input_rnd_idx = perm[int(fraction_missing*fm*n):int(fraction_missing*(fm+fr)*n)]
        target_rnd_idx = perm2[int(fraction_missing*fm*n):int(fraction_missing*(fm+fr)*n)] 
        inp = code.clone()
        target = code.clone()
        inp[input_rnd_idx] = target[target_rnd_idx]
        target[delete_target_idx] = -1
        inp[delete_input_idx] = -1
        #print(inp)
        #print(target)
        inputs += [inp]
        targets += [target]
        masks_input += [mask_input]
        masks_target += [mask_target]
    return inputs, targets, masks_input, masks_target


def BERTize(codes, fraction_missing=0.15, fraction_mask=0.8, fraction_rand=0.1, window=[-2, -1, 0, 1, 2]):
    """
    Not pure random, if an edge is deleted also delete the 2 adjacent edges.
    
    Training the language model in BERT is done by predicting 15% of the tokens in the input, that were randomly picked. 
    These tokens are pre-processed as follows — 80% are replaced with a “[MASK]” token, 10% with a random word, and 10% 
    use the original word. 
    
    to get a random word we use the following strategy: we copy an random entry to that position 
    
    returns preprocessed input sequences, target sequences and a mask indicating which inputs are part of the 15% masked, orig, rnd
    """
    fraction_orig = 1. - fraction_mask - fraction_rand
    fo = fraction_orig
    fm = fraction_mask
    fr = fraction_rand
    inputs = []
    targets = []
    masks_input = []
    masks_target = []
    for code in codes:
        n = len(code)
        # affected inputs
        # at least delete 1
        n_anchors = max(1, int(n * (1/len(window)) * fraction_missing)) # fraction missing should really be renamed to fraction affected
        perm = np.random.permutation(n)
        anchors = perm[:n_anchors]
        affected = []
        for anchor in anchors:
            for offset in window:
                idx = anchor+offset
                if idx >= 0 and idx < n:
                    affected += [idx]
        indices_affected = np.random.permutation(affected)
        n_aff = len(indices_affected)
        delete_input_idx = indices_affected[:int(fm*n_aff)]
        delete_target_idx = np.asarray(list(set(range(n)) - set(affected)))
        input_rnd_idx = indices_affected[int(fm*n_aff):int((fm+fr)*n_aff)]
        target_rnd_idx = np.random.permutation(n)[int(fm*n_aff):int((fm+fr)*n_aff)]
        inp = code.clone()
        target = code.clone()
        inp[input_rnd_idx] = target[target_rnd_idx]
        target[delete_target_idx] = -1
        inp[delete_input_idx] = -1
        inputs += [inp]
        targets += [target]
        mask_input = torch.zeros(n, dtype=bool)
        mask_target = torch.zeros(n, dtype=bool)
        mask_input[delete_input_idx] = True
        mask_input = ~mask_input
        mask_target[indices_affected] = True
        masks_input += [mask_input]
        masks_target += [mask_target]
    return inputs, targets, masks_input, masks_target


def collate_BERT(dlist, mode="rnd2rnd", fraction_missing=0.15, use_loops=False, window=[0]): # window [-1, 0, 1] can be used to delete chunks
        node_batch = [] 
        edge_batch = []
        code_batch = []
        dfs_codes = defaultdict(list)
        if "properties" in dlist[0].keys():
            prop_batch = defaultdict(list)
        if use_loops:
            loop = torch.tensor(bond_features(None)).unsqueeze(0)
        for d in dlist:
            edge_features = d.edge_features
            
            if mode == "min2min":
                code = d.min_dfs_code
                index = d.min_dfs_index
            elif mode == "rnd2rnd":
                rnd_code, rnd_index = dfs_code.rnd_dfs_code_from_torch_geometric(d, 
                                                                         d.z.numpy().tolist(), 
                                                                         np.argmax(d.edge_attr.numpy(), axis=1))                
                code = torch.tensor(rnd_code)
                index = torch.tensor(rnd_index)
            else:
                raise ValueError("unknown config.training.mode %s"%mode)
                
            if use_loops:
                edge_features = torch.cat((edge_features, loop), dim=0)
                vids = torch.argsort(index).unsqueeze(1)
                eids = torch.ones_like(vids)*(edge_features.shape[0] - 1)
                nattr = d.z[vids]
                eattr = torch.ones_like(vids)*4 # 4 stands for loop
                arange = index[vids]
                loops = torch.cat((arange, arange, nattr, eattr, nattr, vids, eids, vids), dim=1)
                code = torch.cat((code, loops), dim=0)
                
            node_batch += [d.node_features]
            edge_batch += [edge_features]
            code_batch += [code]
            if "properties" in dlist[0].keys():
                for name, prop in d.properties.items():
                    prop_batch[name.replace('_', '.')] += [prop]
                    
        inputs, outputs, masks_input, masks_output = BERTize(code_batch, fraction_missing=fraction_missing, window=window)
        dfs_codes_input = dfs_codes_to_dicts(inputs, node_batch, edge_batch, masks_input, padding_value=-1000)
        dfs_codes_output = dfs_codes_to_dicts(outputs, node_batch, edge_batch, masks_output, padding_value=-1)
        dfs_codes_output = FeaturizedDFSCodes2Dict(dfs_codes_output)
        
        if "properties" in dlist[0].keys():
            prop_batch = {name: torch.tensor(plist).clone() for name, plist in prop_batch.items()}
            return dfs_codes_input, dfs_codes_output, prop_batch
        return dfs_codes_input, dfs_codes_output
    

def collate_delete_one(dlist, mode="rnd2rnd", fraction_missing=0.15, use_loops=False, del_idx=[0]):
        node_batch = [] 
        edge_batch = []
        code_batch = []
        dfs_codes = defaultdict(list)
        if "properties" in dlist[0].keys():
            prop_batch = defaultdict(list)
        if use_loops:
            loop = torch.tensor(bond_features(None)).unsqueeze(0)
        for d in dlist:
            edge_features = d.edge_features
            
            if mode == "min2min":
                code = d.min_dfs_code
                index = d.min_dfs_index
            elif mode == "rnd2rnd":
                rnd_code, rnd_index = dfs_code.rnd_dfs_code_from_torch_geometric(d, 
                                                                         d.z.numpy().tolist(), 
                                                                         np.argmax(d.edge_attr.numpy(), axis=1))                
                code = torch.tensor(rnd_code)
                index = torch.tensor(rnd_index)
            else:
                raise ValueError("unknown config.training.mode %s"%mode)
                
            if use_loops:
                edge_features = torch.cat((edge_features, loop), dim=0)
                vids = torch.argsort(index).unsqueeze(1)
                eids = torch.ones_like(vids)*(edge_features.shape[0] - 1)
                nattr = d.z[vids]
                eattr = torch.ones_like(vids)*4 # 4 stands for loop
                arange = index[vids]
                loops = torch.cat((arange, arange, nattr, eattr, nattr, vids, eids, vids), dim=1)
                code = torch.cat((code, loops), dim=0)
                
            node_batch += [d.node_features]
            edge_batch += [edge_features]
            code_batch += [code]
            if "properties" in dlist[0].keys():
                for name, prop in d.properties.items():
                    prop_batch[name.replace('_', '.')] += [prop]
        
        inputs, outputs, masks_input, masks_output = BERTize(code_batch, fraction_missing=0.)
        for idx, (inp, out, mask_inp, mask_out) in enumerate(zip(inputs, outputs, masks_input, masks_output)):
            out = inp.clone()
            mask = torch.zeros(len(inp), dtype=torch.bool)
            for didx in del_idx:
                if didx < len(mask):
                    mask[didx] = True
            inp[mask] = -1
            out[~mask] = -1
            inputs[idx] = inp
            outputs[idx] = out
            masks_input[idx] = ~mask
            masks_output[idx] = mask
                
        dfs_codes_input = dfs_codes_to_dicts(inputs, node_batch, edge_batch, masks_input, padding_value=-1000)
        dfs_codes_output = dfs_codes_to_dicts(outputs, node_batch, edge_batch, masks_output, padding_value=-1)
        dfs_codes_output = FeaturizedDFSCodes2Dict(dfs_codes_output)
        
        if "properties" in dlist[0].keys():
            prop_batch = {name: torch.tensor(plist).clone() for name, plist in prop_batch.items()}
            return dfs_codes_input, dfs_codes_output, prop_batch
        return dfs_codes_input, dfs_codes_output
    
    
def collate_rnd2min(dlist, use_loops=False):
    raise NotImplemented("this never got updated")
    node_batch = [] 
    edge_batch = []
    min_code_batch = []
    rnd_code_batch = []
    if "properties" in dlist[0].keys:
        prop_batch = defaultdict(list)
    if use_loops:
        loop = torch.tensor(bond_features(None)).unsqueeze(0)
    for d in dlist:
        edge_features = d.edge_features.clone()
        min_code = d.min_dfs_code.clone()
        rnd_code, rnd_index = dfs_code.rnd_dfs_code_from_torch_geometric(d, 
                                                                 d.z.numpy().tolist(), 
                                                                 np.argmax(d.edge_attr.numpy(), axis=1))
        rnd_code = torch.tensor(rnd_code)
        if use_loops:
            edge_features = torch.cat((edge_features, loop), dim=0)
            min_vids = torch.argsort(d.min_dfs_index).unsqueeze(1)
            rnd_vids = torch.argsort(torch.tensor(rnd_index, dtype=torch.long)).unsqueeze(1)
            eids = torch.ones_like(min_vids)*(edge_features.shape[0] - 1)
            min_nattr = d.z[min_vids]
            rnd_nattr = d.z[rnd_vids]
            eattr = torch.ones_like(min_vids)*4 # 4 stands for loop
            arange = d.min_dfs_index[min_vids]

            min_loops = torch.cat((arange, arange, min_nattr, eattr, min_nattr, min_vids, eids, min_vids), dim=1)
            rnd_loops = torch.cat((arange, arange, rnd_nattr, eattr, rnd_nattr, rnd_vids, eids, rnd_vids), dim=1)
            min_code = torch.cat((min_code, min_loops), dim=0)
            rnd_code = torch.cat((rnd_code, rnd_loops), dim=0)

        node_batch += [d.node_features.clone()]
        edge_batch += [edge_features]
        min_code_batch += [min_code]
        rnd_code_batch += [rnd_code]
        if "properties" in dlist[0].keys:
            for name, prop in d.properties.items():
                prop_batch[name] += [prop]
    targets = nn.utils.rnn.pad_sequence(min_code_batch, padding_value=-1)
    if "properties" in dlist[0].keys:
        prop_batch = {name: torch.tensor(deepcopy(plist)) for name, plist in prop_batch.items()}
        return rnd_code_batch, node_batch, edge_batch, targets, prop_batch
    return rnd_code_batch, node_batch, edge_batch, targets 

    
def collate_downstream(dlist, alpha=0, use_loops=False, use_min=False):
    dfs_codes = defaultdict(list)
    smiles = []
    node_batch = [] 
    edge_batch = []
    y_batch = []
    rnd_code_batch = []
    if use_loops:
        loop = torch.tensor(bond_features(None)).unsqueeze(0)
    for d in dlist:
        edge_features = d.edge_features.clone()
        if use_min:
            code = d.min_dfs_code.clone()
            index = d.min_dfs_index.clone()
        else:
            code, index = dfs_code.rnd_dfs_code_from_torch_geometric(d, d.z.numpy().tolist(), 
                                                                     np.argmax(d.edge_attr.numpy(), axis=1).tolist())
            
            code = torch.tensor(np.asarray(code), dtype=torch.long)
            index = torch.tensor(np.asarray(index), dtype=torch.long)
        
        if use_loops:
            edge_features = torch.cat((edge_features, loop), dim=0)
            vids = torch.argsort(index).unsqueeze(1)
            eids = torch.ones_like(vids)*(edge_features.shape[0] - 1)
            nattr = d.z[vids]
            eattr = torch.ones_like(vids)*4 # 4 stands for loop
            arange = index[vids]
            loops = torch.cat((arange, arange, nattr, eattr, nattr, vids, eids, vids), dim=1)
            code = torch.cat((code, loops), dim=0).clone()
        
        rnd_code_batch += [code]
        node_batch += [d.node_features.clone()]
        edge_batch += [edge_features]
        y_batch += [d.y.clone()]
        smiles += [deepcopy(d.smiles)]        
    y = torch.cat(y_batch).unsqueeze(1)
    y = (1-alpha)*y + alpha/2
    
    for inp, nfeats, efeats in zip(rnd_code_batch, node_batch, edge_batch):
        dfs_codes['dfs_from'] += [inp[:, 0]]
        dfs_codes['dfs_to'] += [inp[:, 1]]
        atm_from_feats = nfeats[inp[:, -3]]
        atm_to_feats = nfeats[inp[:, -1]]
        bnd_feats = efeats[inp[:, -2]]
        dfs_codes['atm_from'] += [atm_from_feats]
        dfs_codes['atm_to'] += [atm_to_feats]
        dfs_codes['bnd'] += [bnd_feats]

    dfs_codes = {key: nn.utils.rnn.pad_sequence(values, padding_value=-1000).clone()
                 for key, values in dfs_codes.items()}
    return smiles, dfs_codes, y


def collate_downstream_qm9(dlist, alpha=0, use_loops=False, use_min=False):
    dfs_codes = defaultdict(list)
    smiles = []
    node_batch = [] 
    edge_batch = []
    z_batch = []
    y_batch = []
    rnd_code_batch = []
    if use_loops:
        loop = torch.tensor(bond_features(None)).unsqueeze(0)
    for d in dlist:
        edge_features = d.edge_features.clone()
        if use_min:
            code = d.min_dfs_code.clone()
            index = d.min_dfs_index.clone()
        else:
            code, index = dfs_code.rnd_dfs_code_from_torch_geometric(d, d.z.numpy().tolist(), 
                                                                     np.argmax(d.edge_attr.numpy(), axis=1).tolist())
            
            code = torch.tensor(np.asarray(code), dtype=torch.long)
            index = torch.tensor(np.asarray(index), dtype=torch.long)
        
        if use_loops:
            edge_features = torch.cat((edge_features, loop), dim=0)
            vids = torch.argsort(index).unsqueeze(1)
            eids = torch.ones_like(vids)*(edge_features.shape[0] - 1)
            nattr = d.z[vids]
            eattr = torch.ones_like(vids)*4 # 4 stands for loop
            arange = index[vids]
            loops = torch.cat((arange, arange, nattr, eattr, nattr, vids, eids, vids), dim=1)
            code = torch.cat((code, loops), dim=0).clone()
        
        rnd_code_batch += [code]
        node_batch += [d.node_features.clone()]
        edge_batch += [edge_features]
        y_batch += [d.y.clone()]
        smiles += [deepcopy(d.smiles)]        
        z_batch += [d.z.clone().unsqueeze(0)]
    z = torch.cat(z_batch, dim=0)
    y = torch.cat(y_batch).unsqueeze(1)
    y = (1-alpha)*y + alpha/2
    
    for inp, nfeats, efeats in zip(rnd_code_batch, node_batch, edge_batch):
        dfs_codes['dfs_from'] += [inp[:, 0]]
        dfs_codes['dfs_to'] += [inp[:, 1]]
        atm_from_feats = nfeats[inp[:, -3]]
        atm_to_feats = nfeats[inp[:, -1]]
        bnd_feats = efeats[inp[:, -2]]
        dfs_codes['atm_from'] += [atm_from_feats]
        dfs_codes['atm_to'] += [atm_to_feats]
        dfs_codes['bnd'] += [bnd_feats]

    dfs_codes = {key: nn.utils.rnn.pad_sequence(values, padding_value=-1000).clone()
                 for key, values in dfs_codes.items()}
    return smiles, dfs_codes, z,  y

def collate_Barlow(dlist, use_loops=False):
    smiles = []
    node_batch = [] 
    edge_batch = []
    y_batch = []
    rnd_code_batch = []
    min_code_batch = []
    if use_loops:
        loop = torch.tensor(bond_features(None)).unsqueeze(0)
    for d in dlist:
        edge_features = d.edge_features.clone()
        min_code = d.min_dfs_code.clone()
        min_index = d.min_dfs_index.clone()
        code, index = dfs_code.rnd_dfs_code_from_torch_geometric(d, d.z.numpy().tolist(), 
                                                                 np.argmax(d.edge_attr.numpy(), axis=1).tolist())
        
        rnd_code = torch.tensor(np.asarray(code), dtype=torch.long)
        rnd_index = torch.tensor(np.asarray(index), dtype=torch.long)
        
        if use_loops:
            raise NotImplementedError("this functionality is not implemented yet")
        
        rnd_code_batch += [rnd_code]
        min_code_batch += [min_code]
        node_batch += [d.node_features.clone()]
        edge_batch += [edge_features]
    
    min_dfs_codes = dfs_codes_to_dicts(min_code_batch, node_batch, edge_batch)
    rnd_dfs_codes = dfs_codes_to_dicts(rnd_code_batch, node_batch, edge_batch)
    return min_dfs_codes, rnd_dfs_codes


def BERTize_entries(code, fraction_missing=0.15, fraction_mask=0.8, fraction_rand=0.1):
    """
    @param code: a dfs code with entries (dfs1, dfs2, atm1, bnd, atm2, idx1, eidx, idx2)
    
    Training the language model in BERT is done by predicting 15% of the tokens in the input, that were randomly picked. 
    These tokens are pre-processed as follows — 80% are replaced with a “[MASK]” token, 10% with a random word, and 10% 
    use the original word. 
    
    to get a random word we use the following strategy: we copy an random entry to that position 
    TODO: in the future one could also in addition implement a flip of the edge direction with a 50% chance
    
    returns preprocessed input sequences, target sequences and a mask indicating which inputs are part of the 15% masked, orig, rnd
    """
    fraction_orig = 1. - fraction_mask - fraction_rand
    fo = fraction_orig
    fm = fraction_mask
    fr = fraction_rand
    n = len(code)
    mask = np.random.binomial(1, fraction_missing, code.shape).astype(bool)
    mask_delete = np.random.binomial(1, fraction_mask, code.shape).astype(bool)*mask
    mask_random_inp = np.random.binomial(1, fraction_rand/(1-fm), code.shape).astype(bool)*(True^mask_delete)*mask
    mask_random_out = mask_random_inp.copy()
    mask_random_out[:, 0] = mask_random_out[np.random.permutation(n), 0]
    mask_random_out[:, 1] = mask_random_out[np.random.permutation(n), 1]
    mask_random_out[:, 2] = mask_random_out[np.random.permutation(n), 2]
    mask_random_out[:, 3] = mask_random_out[np.random.permutation(n), 3]
    mask_random_out[:, 4] = mask_random_out[np.random.permutation(n), 4]
    mask = torch.tensor(mask)
    mask_delete = torch.tensor(mask_delete)
    mask_random_inp = torch.tensor(mask_random_inp)
    mask_random_out = torch.tensor(mask_random_out)
    mask_delete[:, -3:] = False
    inp = code.clone()
    target = code.clone()
    inp[mask_random_inp[:, 0], 0] = target[mask_random_out[:, 0], 0]
    inp[mask_random_inp[:, 1], 1] = target[mask_random_out[:, 1], 1]
    inp[mask_random_inp[:, 2], 2] = target[mask_random_out[:, 2], 2]
    inp[mask_random_inp[:, 3], 3] = target[mask_random_out[:, 3], 3]
    inp[mask_random_inp[:, 4], 4] = target[mask_random_out[:, 4], 4]
    inp[mask_random_inp[:, 2], 5] = target[mask_random_out[:, 2], 5]
    inp[mask_random_inp[:, 3], 6] = target[mask_random_out[:, 3], 6]
    inp[mask_random_inp[:, 4], 7] = target[mask_random_out[:, 4], 7]
    # it needs to be done like tihs because there are also dimensions 5-7...
    target[~mask] = -1
    inp[mask_delete] = -1
    return inp, target, mask_delete

def collate_BERT_entries(dlist, mode="rnd2rnd", fraction_missing=0.15, use_loops=False):
        if use_loops:
            raise NotImplementedError("did not implement this yet")
        
        outputs = []
        dfs_codes = defaultdict(list)
        if "properties" in dlist[0].keys():
            prop_batch = defaultdict(list)
        if use_loops:
            loop = torch.tensor(bond_features(None)).unsqueeze(0)
        for d in dlist:
            
            edge_features = d.edge_features
            
            if mode == "min2min":
                code = d.min_dfs_code
                index = d.min_dfs_index
            elif mode == "rnd2rnd":
                rnd_code, rnd_index = dfs_code.rnd_dfs_code_from_torch_geometric(d, 
                                                                         d.z.numpy().tolist(), 
                                                                         np.argmax(d.edge_attr.numpy(), axis=1))                
                code = torch.tensor(rnd_code)
                index = torch.tensor(rnd_index)
            else:
                raise ValueError("unknown config.training.mode %s"%mode)
                

            if "properties" in dlist[0].keys():
                for name, prop in d.properties.items():
                    prop_batch[name.replace('_', '.')] += [prop]
            
            inp, out, bertmask = BERTize_entries(code, fraction_missing=fraction_missing)
            outputs += [out]
            nfeats = d.node_features
            efeats = edge_features
            mask = ~bertmask # the mask returned by BERT indicates which inputs will be masked away
            dfs_codes['dfs_from'] += [inp[:, 0]]
            dfs_codes['dfs_to'] += [inp[:, 1]]
            
            atm_from_feats = torch.ones((inp.shape[0], nfeats.shape[1]))
            atm_from_feats[mask[:, 2]] *= nfeats[inp[mask[:, 2]][:, -3]]
            atm_from_feats[~mask[:, 2]] *= -1
            
            atm_to_feats = torch.ones((inp.shape[0], nfeats.shape[1]))
            atm_to_feats[mask[:, 4]] *= nfeats[inp[mask[:, 4]][:, -1]]
            atm_to_feats[~mask[:, 4]] *= -1
            
            bnd_feats = torch.ones((inp.shape[0], efeats.shape[1]))
            bnd_feats[mask[:, 3]] *= efeats[inp[mask[:, 3]][:, -2]]
            bnd_feats[~mask[:, 3]] *= -1
            
            
            dfs_codes['atm_from'] += [atm_from_feats]
            dfs_codes['atm_to'] += [atm_to_feats]
            dfs_codes['bnd'] += [bnd_feats]
            
        dfs_codes = {key: nn.utils.rnn.pad_sequence(values, padding_value=-1000).clone()
                     for key, values in dfs_codes.items()}
        
        targets = nn.utils.rnn.pad_sequence(outputs, padding_value=-1).clone()
        if "properties" in dlist[0].keys():
            prop_batch = {name: torch.tensor(plist).clone() for name, plist in prop_batch.items()}
            return dfs_codes, targets, prop_batch
        return dfs_codes, targets
