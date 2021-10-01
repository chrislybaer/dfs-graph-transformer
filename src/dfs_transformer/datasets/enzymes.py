#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 15:27:25 2021

@author: chrisw
"""
from torch.utils.data import Dataset
from torch_geometric.data import Data
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import pickle

acids2int = {'ALA': 0,
 'ARG': 1,
 'ASN': 2,
 'ASP': 3,
 'ASX': 4,
 'CYS': 5,
 'GLN': 6,
 'GLU': 7,
 'GLX': 8,
 'GLY': 9,
 'HIS': 10,
 'ILE': 11,
 'LEU': 12,
 'LYS': 13,
 'MET': 14,
 'PHE': 15,
 'PYL': 16,
 'SEC': 17,
 'SER': 18,
 'THR': 19,
 'TRP': 20,
 'TYR': 21,
 'VAL': 22,
 'XAA': 23,
 'XLE': 24,
 'others': 25}
acids2int_200 = {'0ZZ': 0,
 '1KU': 1,
 '1KY': 2,
 '21V': 3,
 '2CO': 4,
 '384': 5,
 '3CN': 6,
 '3CT': 7,
 '3NZ': 8,
 '3TL': 9,
 '3TZ': 10,
 '4PH': 11,
 '57Y': 12,
 '6B4': 13,
 '6V1': 14,
 '8DM': 15,
 'A3G': 16,
 'A3S': 17,
 'A3T': 18,
 'AG2': 19,
 'ALA': 20,
 'ALY': 21,
 'AME': 22,
 'ARG': 23,
 'ASN': 24,
 'ASP': 25,
 'BCS': 26,
 'BFD': 27,
 'BH2': 28,
 'BHD': 29,
 'BIF': 30,
 'BQL': 31,
 'BQO': 32,
 'BYR': 33,
 'CA': 34,
 'CAF': 35,
 'CAS': 36,
 'CFD': 37,
 'CGA': 38,
 'CGU': 39,
 'CME': 40,
 'CSD': 41,
 'CSO': 42,
 'CSS': 43,
 'CSX': 44,
 'CXM': 45,
 'CYS': 46,
 'D3Y': 47,
 'DDF': 48,
 'DHF': 49,
 'DR7': 50,
 'DSN': 51,
 'EA4': 52,
 'ELA': 53,
 'FFO': 54,
 'FHF': 55,
 'FLC': 56,
 'FME': 57,
 'FOL': 58,
 'G7H': 59,
 'G7N': 60,
 'GCH': 61,
 'GLN': 62,
 'GLU': 63,
 'GLY': 64,
 'GNB': 65,
 'HIP': 66,
 'HIS': 67,
 'IAS': 68,
 'ILE': 69,
 'KJZ': 70,
 'LA2': 71,
 'LEU': 72,
 'LYS': 73,
 'MDB': 74,
 'MET': 75,
 'MHO': 76,
 'MLY': 77,
 'MLZ': 78,
 'MME': 79,
 'MOT': 80,
 'MSE': 81,
 'MTX': 82,
 'NCB': 83,
 'NEP': 84,
 'NIY': 85,
 'OCS': 86,
 'OLD': 87,
 'ONA': 88,
 'P34': 89,
 'PCA': 90,
 'PHD': 91,
 'PHE': 92,
 'PHI': 93,
 'PLM': 94,
 'PRO': 95,
 'PTR': 96,
 'SAH': 97,
 'SAM': 98,
 'SC2': 99,
 'SE7': 100,
 'SEC': 101,
 'SEP': 102,
 'SER': 103,
 'SMC': 104,
 'SME': 105,
 'SMM': 106,
 'SNC': 107,
 'THR': 108,
 'TJ2': 109,
 'TPO': 110,
 'TRP': 111,
 'TYR': 112,
 'UDB': 113,
 'UHF': 114,
 'UMQ': 115,
 'UNK': 116,
 'VAL': 117,
 'XCN': 118,
 'XX1': 119,
 'YCM': 120,
 'YOF': 121}
acids2int_all = {'BWS': 0,
 'DP9': 1,
 '4JK': 2,
 'Y3U': 3,
 'CSB': 4,
 'G7H': 5,
 'SSA': 6,
 'FFO': 7,
 '0RJ': 8,
 'SMX': 9,
 'PRI': 10,
 'MLE': 11,
 'GGB': 12,
 'ORN': 13,
 'T11': 14,
 'EA4': 15,
 'LA2': 16,
 '3TG': 17,
 'PP3': 18,
 'FY3': 19,
 'AZY': 20,
 'CTJ': 21,
 'CCS': 22,
 '384': 23,
 'UDB': 24,
 '4CS': 25,
 'PHD': 26,
 'SA8': 27,
 'M0H': 28,
 'G5A': 29,
 'TYX': 30,
 'G7N': 31,
 'DLY': 32,
 'S4M': 33,
 'SFG': 34,
 'K5H': 35,
 'ONA': 36,
 'MED': 37,
 '1S6': 38,
 'THH': 39,
 'MDB': 40,
 '3CN': 41,
 'FYA': 42,
 'C2F': 43,
 'NAL': 44,
 'MTY': 45,
 'ASX': 46,
 'CSD': 47,
 'BMD': 48,
 'GLN': 49,
 'S2C': 50,
 'HSO': 51,
 'THR': 52,
 'ONL': 53,
 'ATA': 54,
 'HAM': 55,
 'UNK': 56,
 'FZS': 57,
 'BQL': 58,
 'F3V': 59,
 'PLT': 60,
 'MSE': 61,
 'SAM': 62,
 '4U5': 63,
 'SLZ': 64,
 '6M6': 65,
 'OAS': 66,
 'APK': 67,
 '4TM': 68,
 'TYE': 69,
 'GIO': 70,
 'KAA': 71,
 'GSN': 72,
 '5VW': 73,
 '6NA': 74,
 '5CR': 75,
 'NVU': 76,
 'D3Y': 77,
 '6WY': 78,
 '29W': 79,
 'CXM': 80,
 '78U': 81,
 'C3E': 82,
 'X2W': 83,
 'SEE': 84,
 'FOZ': 85,
 'BGT': 86,
 'AMO': 87,
 'OLD': 88,
 'ABH': 89,
 'PMH': 90,
 'MTX': 91,
 'ELA': 92,
 'SMC': 93,
 'FME': 94,
 'CYS': 95,
 'PDG': 96,
 '51T': 97,
 'A5A': 98,
 'FOL': 99,
 '0QL': 100,
 'BYR': 101,
 '1JY': 102,
 '5CA': 103,
 'CA': 104,
 'KJZ': 105,
 'ARG': 106,
 'PAO': 107,
 'BIF': 108,
 'TYP': 109,
 '59F': 110,
 'WSA': 111,
 'CGV': 112,
 'PYW': 113,
 'IVA': 114,
 'HIQ': 115,
 'CYG': 116,
 'NLG': 117,
 'HTI': 118,
 'P34': 119,
 'A3T': 120,
 'DHL': 121,
 '01K': 122,
 'VAH': 123,
 '15U': 124,
 '1D0': 125,
 'CSX': 126,
 'PHI': 127,
 'MIS': 128,
 'SC2': 129,
 'HCS': 130,
 '4CF': 131,
 'BPE': 132,
 'AHL': 133,
 'SNC': 134,
 'XX1': 135,
 'IAS': 136,
 'MPH': 137,
 'ME8': 138,
 'EVA': 139,
 '4PH': 140,
 'MHO': 141,
 'SCH': 142,
 'N15': 143,
 'DSH': 144,
 'NVA': 145,
 'PPD': 146,
 'CAS': 147,
 '5BA': 148,
 'MLY': 149,
 'LOH': 150,
 'LSS': 151,
 'NLQ': 152,
 'PBC': 153,
 'PGU': 154,
 'FGA': 155,
 'BZ7': 156,
 'NHL': 157,
 '2RG': 158,
 'KPI': 159,
 'UHF': 160,
 'MSP': 161,
 'PFV': 162,
 'LYS': 163,
 'LTN': 164,
 'YOF': 165,
 'KPA': 166,
 'DSN': 167,
 'FOO': 168,
 '3CT': 169,
 'ALA': 170,
 'A3G': 171,
 'TYI': 172,
 'HQ5': 173,
 'BQO': 174,
 'CGU': 175,
 'FZQ': 176,
 'ABU': 177,
 'ILE': 178,
 'TSB': 179,
 'TRP': 180,
 '200': 181,
 '0A0': 182,
 'RF9': 183,
 'HYP': 184,
 'DAH': 185,
 'SEC': 186,
 'MME': 187,
 'KGC': 188,
 'EVM': 189,
 'LYN': 190,
 'PUY': 191,
 'BBC': 192,
 'YOL': 193,
 'FZK': 194,
 'PL2': 195,
 'PHE': 196,
 'CFD': 197,
 'BH2': 198,
 'OMT': 199,
 'PTR': 200,
 '2P0': 201,
 'AAT': 202,
 'CHQ': 203,
 '1RG': 204,
 'SVA': 205,
 'PSD': 206,
 'LAD': 207,
 'AL0': 208,
 '2OP': 209,
 'SRP': 210,
 'Z72': 211,
 'D16': 212,
 'C6P': 213,
 'FA5': 214,
 'BCS': 215,
 'LYF': 216,
 'F2Y': 217,
 'OCY': 218,
 'IBO': 219,
 'OHI': 220,
 'ASP': 221,
 'CSO': 222,
 'NLP': 223,
 'TEF': 224,
 'TMF': 225,
 'TPO': 226,
 '0Y2': 227,
 '7TS': 228,
 'M3L': 229,
 '15S': 230,
 'GNB': 231,
 '37M': 232,
 '1KV': 233,
 'MLZ': 234,
 'EPC': 235,
 'CSS': 236,
 'MPJ': 237,
 'TJ2': 238,
 'SCS': 239,
 '0GJ': 240,
 'SMM': 241,
 '3NZ': 242,
 '8DM': 243,
 'DGN': 244,
 'NPQ': 245,
 '3TL': 246,
 '3Y6': 247,
 'MLL': 248,
 'NHR': 249,
 'ASL': 250,
 '0JO': 251,
 '4OV': 252,
 'TFB': 253,
 'N13': 254,
 'ASN': 255,
 'SME': 256,
 '8VS': 257,
 'PLM': 258,
 'LSU': 259,
 'DJD': 260,
 'T8L': 261,
 'CB3': 262,
 'YSC': 263,
 '4OU': 264,
 'NCB': 265,
 'OSE': 266,
 'RB6': 267,
 '74P': 268,
 'SEP': 269,
 'AS2': 270,
 'DR7': 271,
 'MHF': 272,
 'KYQ': 273,
 'A3S': 274,
 '8RE': 275,
 'LYO': 276,
 'SAH': 277,
 'CAF': 278,
 'PBF': 279,
 'SAC': 280,
 'FGF': 281,
 '2UZ': 282,
 'CGE': 283,
 'YPP': 284,
 'GSU': 285,
 'AG3': 286,
 'LLP': 287,
 'AG2': 288,
 'AHB': 289,
 'P5A': 290,
 'YCM': 291,
 'B3K': 292,
 'TYA': 293,
 'DDF': 294,
 '1KU': 295,
 '0HG': 296,
 'AEI': 297,
 '0G6': 298,
 'CSU': 299,
 'AHN': 300,
 'HSL': 301,
 'DAS': 302,
 'LEU': 303,
 'AKR': 304,
 'HIC': 305,
 'NNH': 306,
 'L3U': 307,
 'C8V': 308,
 'ILP': 309,
 'ALO': 310,
 'MET': 311,
 'GSO': 312,
 'CZ7': 313,
 '0A1': 314,
 'HIS': 315,
 'ALJ': 316,
 '2LT': 317,
 'HSS': 318,
 'BHD': 319,
 'NFF': 320,
 '4AX': 321,
 'BFD': 322,
 'SEB': 323,
 'VKC': 324,
 'TYM': 325,
 'YSU': 326,
 '85F': 327,
 'HLU': 328,
 'PDA': 329,
 '3GE': 330,
 '21V': 331,
 '80F': 332,
 '0Z6': 333,
 '6V1': 334,
 'REZ': 335,
 'MEF': 336,
 'ONM': 337,
 'HSA': 338,
 'PCA': 339,
 '4BF': 340,
 'THF': 341,
 'HJT': 342,
 'VAL': 343,
 'FTR': 344,
 'VPP': 345,
 '3TZ': 346,
 'C2N': 347,
 'ALY': 348,
 'PSW': 349,
 '0RN': 350,
 'AD8': 351,
 'DWZ': 352,
 'KPF': 353,
 '0HZ': 354,
 'TYR': 355,
 'SER': 356,
 'NEP': 357,
 '6B4': 358,
 'GCH': 359,
 'DGL': 360,
 'SCY': 361,
 'I4I': 362,
 '0ZZ': 363,
 'FZT': 364,
 'KOU': 365,
 'SL5': 366,
 'MOD': 367,
 'F89': 368,
 'NIY': 369,
 '0AK': 370,
 '510': 371,
 'DP1': 372,
 '3YM': 373,
 'FEJ': 374,
 'TIH': 375,
 'KCX': 376,
 'JM7': 377,
 'CSP': 378,
 'FLC': 379,
 'DAB': 380,
 'XD1': 381,
 'DCS': 382,
 'CD7': 383,
 'DON': 384,
 '1KY': 385,
 'FC2': 386,
 '57Y': 387,
 'IYR': 388,
 'HIP': 389,
 'XCN': 390,
 'P1T': 391,
 'THG': 392,
 'CB9': 393,
 'GLY': 394,
 'CME': 395,
 'OCS': 396,
 '2CO': 397,
 'YSA': 398,
 'HAR': 399,
 'PPE': 400,
 'MOT': 401,
 '3RG': 402,
 'SE7': 403,
 'P9S': 404,
 'CS1': 405,
 'GAM': 406,
 'PLS': 407,
 'BAL': 408,
 'AH0': 409,
 'V5X': 410,
 'DAL': 411,
 'P5U': 412,
 '138': 413,
 'NOT': 414,
 'SGI': 415,
 'ZGL': 416,
 '4U6': 417,
 '5AL': 418,
 'ABA': 419,
 'AME': 420,
 '4MV': 421,
 'OZT': 422,
 'FHF': 423,
 'AA5': 424,
 'UMQ': 425,
 'CGA': 426,
 'CMH': 427,
 'GLU': 428,
 'DHF': 429,
 'MSO': 430,
 'PRO': 431,
 'NXL': 432,
 'ASB': 433}
labels2idx = {"4.2.1.10": 0, "6.5.1.1": 1, "4.2.3.1": 2, "2.7.7.48": 3, "3.1.3.25": 4, "3.1.21.4": 5, "3.2.1.23": 6, "6.3.5.3": 7, "4.2.1.20": 8, "3.4.11.18": 9, "6.3.4.18": 10, "3.1.22.4": 11, "2.3.1.87": 12, "2.7.7.3": 13, "3.2.1.4": 14, "2.7.1.2": 15, "3.1.2.2": 16, "7.1.2.2": 17, "2.7.11.12": 18, "3.2.1.3": 19, "1.14.14.18": 20, "4.1.1.20": 21, "2.8.1.12": 22, "3.5.2.6": 23, "4.6.1.2": 24, "6.1.1.3": 25, "1.14.16.1": 26, "2.1.1.220": 27, "2.7.7.60": 28, "3.4.21.92": 29, "1.1.1.100": 30, "4.2.1.84": 31, "2.8.1.7": 32, "5.6.1.1": 33, "4.2.2.2": 34, "2.4.1.18": 35, "3.4.22.60": 36, "3.6.1.7": 37, "6.3.4.4": 38, "6.1.1.19": 39, "1.12.99.6": 40, "4.2.99.18": 41, "3.2.1.1": 42, "6.1.1.15": 43, "1.14.13.225": 44, "3.2.1.37": 45, "5.3.1.23": 46, "3.2.2.27": 47, "2.7.7.6": 48, "1.18.6.1": 49, "6.1.1.20": 50, "3.4.21.107": 51, "3.4.21.90": 52, "1.11.1.7": 53, "3.5.2.3": 54, "4.6.1.18": 55, "2.7.1.39": 56, "7.2.1.1": 57, "2.7.4.22": 58, "3.2.1.41": 59, "2.5.1.19": 60, "3.5.4.16": 61, "2.5.1.18": 62, "2.7.1.33": 63, "2.7.4.8": 64, "4.1.1.23": 65, "1.3.1.98": 66, "2.4.2.10": 67, "1.1.1.1": 68, "2.3.1.57": 69, "2.5.1.47": 70, "2.4.2.19": 71, "4.6.1.19": 72, "2.7.11.30": 73, "2.7.1.15": 74, "2.3.3.8": 75, "2.7.11.13": 76, "3.4.21.104": 77, "2.7.7.9": 78, "5.6.2.1": 79, "4.1.1.48": 80, "2.4.2.17": 81, "1.3.5.2": 82, "2.7.4.6": 83, "3.1.3.48": 84, "2.3.1.48": 85, "1.1.1.2": 86, "2.7.11.22": 87, "4.2.1.22": 88, "5.3.4.1": 89, "3.5.1.2": 90, "5.6.2.2": 91, "6.1.1.1": 92, "7.1.1.1": 93, "3.1.3.7": 94, "4.2.1.96": 95, "4.1.1.11": 96, "2.7.2.4": 97, "3.6.1.34": 98, "2.4.1.1": 99, "1.12.7.2": 100, "1.7.1.17": 101, "3.2.1.78": 102, "3.8.1.2": 103, "2.6.1.52": 104, "3.1.1.96": 105, "2.7.7.18": 106, "6.1.1.7": 107, "2.5.1.15": 108, "2.1.2.2": 109, "2.3.1.81": 110, "3.2.1.20": 111, "2.1.1.148": 112, "3.4.11.2": 113, "6.3.2.19": 114, "3.2.1.55": 115, "4.1.3.3": 116, "2.1.1.63": 117, "3.1.3.16": 118, "3.4.24.69": 119, "1.1.1.184": 120, "2.3.2.5": 121, "4.4.1.5": 122, "6.1.1.17": 123, "1.2.1.11": 124, "4.1.1.15": 125, "2.7.8.7": 126, "2.1.1.228": 127, "2.7.7.65": 128, "2.7.7.n1": 129, "5.1.3.13": 130, "3.4.11.1": 131, "4.1.3.27": 132, "2.5.1.10": 133, "1.1.1.267": 134, "3.8.1.5": 135, "3.2.1.18": 136, "3.4.21.21": 137, "3.2.1.21": 138, "3.1.4.53": 139, "1.1.1.169": 140, "3.6.1.1": 141, "4.1.1.50": 142, "1.3.1.9": 143, "6.1.1.2": 144, "3.5.3.1": 145, "3.2.1.81": 146, "4.1.1.39": 147, "7.2.2.10": 148, "3.6.4.6": 149, "3.1.3.45": 150, "3.6.1.32": 151, "7.1.1.8": 152, "3.6.5.2": 153, "3.5.4.4": 154, "2.3.2.23": 155, "2.7.1.71": 156, "3.6.3.14": 157, "2.6.1.1": 158, "3.4.21.41": 159, "4.1.1.19": 160, "2.4.2.18": 161, "1.15.1.1": 162, "6.1.1.12": 163, "2.7.11.25": 164, "4.3.3.7": 165, "1.5.1.3": 166, "6.1.1.4": 167, "3.6.1.13": 168, "2.7.2.1": 169, "4.1.2.25": 170, "4.6.1.16": 171, "2.1.1.13": 172, "2.7.4.9": 173, "4.1.2.13": 174, "3.1.1.4": 175, "3.2.1.52": 176, "1.1.1.3": 177, "4.2.1.1": 178, "3.4.17.19": 179, "2.3.2.26": 180, "3.2.1.24": 181, "3.5.2.17": 182, "4.1.1.33": 183, "3.1.21.2": 184, "3.1.3.11": 185, "5.1.1.1": 186, "3.1.4.17": 187, "4.3.2.2": 188, "5.3.3.2": 189, "3.4.25.1": 190, "3.2.1.22": 191, "3.2.1.73": 192, "1.14.13.25": 193, "2.3.1.129": 194, "2.3.2.27": 195, "7.1.1.2": 196, "2.1.1.37": 197, "3.2.1.8": 198, "1.10.3.1": 199, "5.4.99.25": 200, "1.9.3.1": 201, "3.2.1.169": 202, "1.1.1.103": 203, "4.2.1.17": 204, "3.4.22.15": 205, "6.5.1.3": 206, "3.1.4.11": 207, "3.4.21.4": 208, "2.3.1.9": 209, "3.1.13.4": 210, "1.6.5.2": 211, "2.3.1.180": 212, "3.4.16.4": 213, "2.1.1.193": 214, "2.7.10.1": 215, "4.6.1.1": 216, "2.7.7.4": 217, "2.5.1.78": 218, "3.4.21.22": 219, "6.3.2.3": 220, "3.2.2.1": 221, "2.7.2.3": 222, "3.4.21.89": 223, "6.3.2.4": 224, "3.2.2.22": 225, "5.3.1.1": 226, "2.7.4.3": 227, "2.7.12.1": 228, "1.5.1.2": 229, "3.2.1.31": 230, "3.4.21.53": 231, "3.5.4.5": 232, "2.7.13.3": 233, "6.1.1.21": 234, "1.1.1.205": 235, "4.1.2.4": 236, "6.3.2.6": 237, "2.1.1.45": 238, "3.1.1.3": 239, "3.4.22.56": 240, "2.7.1.23": 241, "1.14.13.39": 242, "3.6.4.12": 243, "3.2.1.14": 244, "3.5.1.28": 245, "6.3.4.21": 246, "2.7.7.49": 247, "3.1.3.18": 248, "1.10.3.2": 249, "1.1.1.35": 250, "2.1.3.2": 251, "4.1.99.3": 252, "1.3.5.1": 253, "2.7.11.17": 254, "2.7.11.24": 255, "2.3.1.41": 256, "3.2.1.113": 257, "2.3.2.31": 258, "2.3.1.5": 259, "5.1.1.3": 260, "1.13.11.24": 261, "1.14.18.1": 262, "1.8.4.11": 263, "2.8.1.1": 264, "6.1.1.6": 265, "3.1.27.3": 266, "2.7.7.19": 267, "1.1.1.27": 268, "1.7.2.1": 269, "2.1.1.182": 270, "3.4.19.12": 271, "2.1.1.77": 272, "2.3.3.10": 273, "2.7.1.1": 274, "3.1.1.1": 275, "2.7.1.4": 276, "5.3.1.6": 277, "2.7.1.11": 278, "1.2.4.4": 279, "1.8.4.8": 280, "1.6.99.1": 281, "3.1.26.5": 282, "1.8.1.4": 283, "2.4.1.15": 284, "1.8.1.7": 285, "2.2.1.6": 286, "3.1.3.8": 287, "6.3.5.2": 288, "2.7.2.8": 289, "4.2.1.52": 290, "3.5.2.9": 291, "1.11.1.10": 292, "3.1.1.72": 293, "2.7.6.1": 294, "2.7.1.20": 295, "6.1.1.10": 296, "2.4.2.7": 297, "3.5.1.11": 298, "1.8.1.9": 299, "3.1.26.4": 300, "1.17.4.1": 301, "1.3.7.7": 302, "2.1.1.354": 303, "3.1.1.31": 304, "1.1.1.25": 305, "3.6.5.5": 306, "4.2.1.113": 307, "1.1.1.37": 308, "2.6.1.9": 309, "1.16.3.1": 310, "3.2.2.9": 311, "3.1.26.3": 312, "6.2.1.5": 313, "2.7.1.107": 314, "2.4.2.9": 315, "2.3.3.13": 316, "7.2.2.8": 317, "3.5.1.5": 318, "2.7.12.2": 319, "2.7.1.21": 320, "2.7.10.2": 321, "2.5.1.17": 322, "2.4.2.1": 323, "2.1.2.10": 324, "5.2.1.8": 325, "2.7.1.24": 326, "2.6.1.42": 327, "1.4.3.5": 328, "2.5.1.16": 329, "5.4.99.5": 330, "1.18.1.2": 331, "2.4.2.30": 332, "2.3.2.13": 333, "3.1.1.29": 334, "3.4.21.42": 335, "3.2.1.96": 336, "2.7.7.7": 337, "3.5.1.98": 338, "2.4.1.25": 339, "4.6.1.12": 340, "4.2.1.59": 341, "1.14.14.1": 342, "1.11.1.6": 343, "3.1.3.3": 344, "3.2.1.26": 345, "2.7.1.35": 346, "6.3.2.1": 347, "3.4.13.9": 348, "5.1.3.2": 349, "3.4.21.5": 350, "3.2.1.17": 351, "2.7.1.40": 352, "3.6.4.13": 353, "1.8.3.2": 354, "1.17.1.8": 355, "3.1.3.1": 356, "2.7.11.1": 357, "3.1.3.5": 358, "2.3.1.286": 359, "2.1.1.72": 360, "2.4.2.8": 361, "3.6.1.9": 362, "6.3.1.20": 363, "2.1.3.3": 364, "3.5.1.88": 365, "3.6.1.3": 366, "3.4.21.6": 367, "3.1.11.2": 368, "1.11.1.15": 369, "1.11.1.9": 370, "3.2.1.39": 371, "3.6.1.23": 372, "2.3.1.39": 373, "6.1.1.11": 374, "2.7.1.69": 375, "3.1.3.2": 376, "2.3.1.12": 377, "3.1.4.35": 378, "1.16.3.2": 379, "1.2.1.3": 380, "3.2.1.91": 381, "3.5.1.1": 382, "2.7.7.8": 383}


class Enzymes(Dataset):
    def __init__(self, path="/mnt/ssd/datasets/enzyme/min_dfs_transformer_preprocessed_n200_dleq4.5.pkl", 
                 n_edge_types=8, acids2int=acids2int):
        # default edge types:
        # 0: <4
        # 1: <5
        # 2: <6
        # 3: <7
        # 4: <8
        # 5: <9
        # 6: <10
        # 7: others
        self.path = path
        self.n_edge_types = n_edge_types
        self.acids2int = acids2int
        self.data = []
        self.prepare()
  
    
    def prepare(self):
        with open(self.path, 'rb') as f:
            graphs = pickle.load(f)
            
        for name, d in graphs.items():
            
            node_features = F.one_hot(torch.tensor(d['node_types'], dtype=torch.long), 
                                      num_classes=len(self.acids2int)).float()
                                      
            edge_features = F.one_hot(torch.tensor(d['edge_types'], dtype=torch.long), 
                                      num_classes=self.n_edge_types).float()
            self.data += [Data(name=name, 
                               edge_index=torch.tensor(d['edge_index'], dtype=torch.long),
                               node_features=node_features,
                               edge_features=edge_features, 
                               min_dfs_code=torch.tensor(d['min_dfs_code']),
                               min_dfs_index=torch.tensor(d['min_dfs_index']), dtype=torch.long,
                               y = labels2idx[d['label']],
                               split = d['split'])]
            
    def __len__(self):
        return len(self.data)
  
    def __getitem__(self, idx):
        return self.data[idx]