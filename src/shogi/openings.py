# -*- coding: UTF8 -*-

from enum import IntEnum
from typing import Optional
from . import kifu
from .game import Game
from ._pattern import Recognizer, RecognizerResult, SFENMap, PositionForPatternRecognition, adjacent_pawns, last_row_pieces

Opening = IntEnum('Opening',
  ['OPPOSING_ROOK', 'THIRD_FILE_ROOK', 'FORTH_FILE_ROOK', 'GOKIGEN_CENTRAL_ROOK', 'DOUBLE_SWINGING_ROOK',
   'FORTH_THIRD_FILE_ROOK_STRATEGY', 'ROOK32_STRATEGY', 'ROOK78_STRATEGY',
   'QUICK_ISHIDA', 'ISHIDA_STYLE', 'MASUDAS_ISHIDA_STYLE', 'TOMAHAWK',
   'SAKATA_OPPOSING_ROOK', 'AMAHIKO_OPPOSING_ROOK', 'DIRECT_OPPOSING_ROOK',
   'HIDE_CHAN_STYLE_CENTRAL_ROOK', 'PRIMITIVE_CENTRAL_ROOK',
   'FUJII_SYSTEM', 'TATEISHI_STYLE',
   'SWINGING_ROOK_MILLENIUM',
   'LEGHORN_SPECIAL', 'BISHOP_EXCHANGE_SWINGING_ROOK',
   'PACMAN', 'BISHOP_PAWN_STRATEGY',
   'TAKADA_STYLE_LEFT_HAND_KING', 'KIM_KIM_GOLD',
   'FIRST_FILE_ROOK', 'FIRST_FILE_ROOK_ANAGUMA',
    #static
   'SLEEVE_ROOK',
   'RIGHT_HAND_FORTH_FILE_ROOK', 'RIGHT_HAND_FORTH_FILE_ROOK_WITH_LEFT_HAND_MINO',
   'CRAB_SILVERS',
   'RIGHT_HAND_KING',
   'DOUBLE_WING_ATTACK', 'DOUBLE_WING_ATTACK_CLIMBING_SILVER',
   'UFO_SILVER',
   'RECLINING_SILVER',
   'BISHOP_EXCHANGE', 'ONE_TURN_LOSS_BISHOP_EXCHANGE', 'BISHOP_EXCHANGE_RECLINING_SILVER', 'BISHOP_EXCHANGE_CLIMBING_SILVER',
   'RAPID_ADVANCING_SILVER',
   'SIDE_PAWN_PICKER', 'PAWN23_STRATEGY', 'BISHOP33_STRATEGY', 'AONO_STYLE', 'YUUKI_STYLE', 'BISHOP45_STRATEGY', 'ROOK85_STRATEGY',
   'CLIMBING_GOLD', 'CLIMBING_SILVER',
   'SAGINOMIYA_JOSEKI', 'IJIMAS_BACK_BISHOP_STRATEGY',
   'MARUYAMA_VACCINE', 'SILVER37_SUPER_RAPID', 'SUPER_RAPID_ATTACK', 'KATO_STYLE_SLEEVE_ROOK',
   'URESINO_STYLE', 'PRIMITIVE_CLIMBING_SILVER', 'MURATA_SYSTEM', 'SPEARING_THE_BIRD',
   'SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE',
   'SILVER_HORNED_SNOW_ROOF',
   'SILVER37_STRATEGY', 'WAKI_SYSTEM', 'MORISHITA_SYSTEM', 'YONENAGA_STYLE_RAPID_ENGAGING_YAGURA', 'NAKAHARA_STYLE_RAPID_ENGAGING_YAGURA', 'YAGURA_CENTRAL_ROOK',
   'WRONG_DIAGONAL_BISHOP', 'DEMON_KILLER',
   #internal usage
    'NONE', 'SWINGING_ROOK'
])

_OPENINGS_D = SFENMap({
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/2P6/9/PP1PPPPPP/1B5R1/LNSGKGSNL w - 4' : Opening.QUICK_ISHIDA,
  #'ln1g1gsnl/1r3k1b1/p1sppp1pp/2p3p2/1p2P4/2P6/PPBP1PPPP/3SRK3/LN1G1GSNL b - 15': Opening.SILVER37_SUPER_RAPID,
  'lnsgkgsnl/4r2+B1/pppp1p1pp/4p1p2/7P1/2P6/PP1PPPP1P/7R1/LNSGKGSNL w B 8': Opening.MARUYAMA_VACCINE,
  'lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B1S3R1/LN1GKGSNL w - 2': Opening.URESINO_STYLE,
  #'lnsgk1snl/1r4gb1/p1ppppppp/9/1p5P1/9/PPPPPPP1P/1BG3SR1/LNS1KG1NL w - 8': Opening.DOUBLE_WING_ATTACK,
  #'ln1gk1snl/1rs3gb1/p1ppppppp/9/1p5P1/9/PPPPPPP1P/1BG3SR1/LNS1KG1NL b - 9': Opening.DOUBLE_WING_ATTACK,
  #'lnsgk1snl/1r4gb1/p1ppppppp/9/7P1/1p7/PPPPPPP1P/1BG3SR1/LNS1KG1NL b - 9': Opening.DOUBLE_WING_ATTACK,
  'lnsgk1snl/6gb1/p1pppp2p/6R2/9/1rP6/P2PPPP1P/1BG6/LNS1KGSNL w 3P2p 16': Opening.SIDE_PAWN_PICKER,
  'lnsgk1snl/6g2/p1ppppb1p/6R2/9/1rP6/P2PPPP1P/1BG6/LNS1KGSNL b 3P2p 17': Opening.BISHOP33_STRATEGY,
  'ln1gk1snl/3s2g2/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsgk2nl/6gs1/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsg2snl/4k1g2/p1ppppb1p/6R2/9/1rP3P2/P2PPP2P/1BG1K4/LNS2GSNL w 3P2p 20': Opening.AONO_STYLE,
  'lnsgk1snl/6g2/p1ppppb1p/6R2/9/1rP6/P2PPPP1P/1BGK5/LNS2GSNL w 3P2p 18': Opening.YUUKI_STYLE,
  'lnsgkgsnl/1r5+B1/pppppp1pp/6p2/9/2P6/PP1PPPPPP/7R1/LNSGKGSNL w B 4': Opening.NONE, #[not BISHOP_EXCHANGE]
  # 'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
  # 'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
})

_OPENINGS_POS_AND_MOVE_D = SFENMap({
  'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12 8h7g' : Opening.BISHOP_EXCHANGE, #[wars/0004]
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/4P4/PPPP1PPPP/1B2R4/LNSGKGSNL w - 4 2h5h': Opening.GOKIGEN_CENTRAL_ROOK, #[wars/0064]
  'lnsgk1snl/6g2/p1pppp2p/6R2/5b3/1rP6/P2PPPP1P/1SG4S1/LN2KG1NL b B4Pp 21 B*4e' : Opening.BISHOP45_STRATEGY, #[wars/0066]
  'lnsgk1snl/6gb1/p1pppp2p/6pR1/9/P1r6/3PPPP1P/1BG6/LNS1KGSNL b 2P3p 17 8f7f': Opening.SIDE_PAWN_PICKER, #[wars/0084]
  'lnsgk1snl/6gb1/p1pppp2p/6pR1/9/P1r6/2BPPPP1P/2G6/LNS1KGSNL w 2P3p 18 8h7g': Opening.BISHOP33_STRATEGY, #[wars/0084]
  #'lnsgk1snl/1r4gb1/p1ppppppp/7P1/1p7/9/PPPPPPP1P/1BG4R1/LNS1KGSNL w - 8 2e2d': Opening.DOUBLE_WING_ATTACK, #[wars/0088]
  #'ln1gk1snl/1rs3gb1/p1pppppp1/8p/1p7/9/PPPPPPPSP/1BG4R1/LNS1KG1NL w P 16 3h2g': Opening.DOUBLE_WING_ATTACK_CLIMBING_SILVER, #[wars/0088]
  'lnsgkgsnl/4r4/pppp1pb1p/6pR1/9/2P1P4/PP1P1PP1P/1S2G4/LN1GK1SNL b B2Pp 17 B*3c': Opening.SUPER_RAPID_ATTACK,
  'lnsgkgs+Rl/4r4/pppp1pb1p/6p2/9/2P1P4/PP1P1PP1P/1S2G4/LN1GK1SNL w BN2Pp 18 2d2a+': Opening.SUPER_RAPID_ATTACK,
  'lnsgkgsnl/1r5b1/pppppp1p1/6p1p/2P6/8P/PP1PPPPP1/1B5R1/LNSGKGSNL w - 6 7f7e': Opening.QUICK_ISHIDA, #[wars/0111]
  'lnsgkg1nl/1r5s1/pppppp1pp/6p2/5B3/2P6/PP1PPPPPP/7R1/LNSGKGSNL w b 6 B*4e': Opening.WRONG_DIAGONAL_BISHOP, #[wars/0141]
  'lnsgk1snl/1r4gb1/p1pppp1pp/6pR1/1p7/2P6/PP1PPPP1P/1BG6/LNS1KGSNL b P 13 P*2c': Opening.PAWN23_STRATEGY,
  #'lnsgkgsnl/1r5b1/p1pp1pppp/4p4/1p2P4/9/PPPP1PPPP/1BG1R4/LNS1KGSNL w - 8 5f5e': Opening.PRIMITIVE_CENTRAL_ROOK, #[mdE98YduMCU]
  #'lnsgk1snl/1r4g2/pppppp1pp/6p2/7P1/2P6/PP1PPPP1P/1+b5R1/LNSGKGSNL b b 7 2b8h+': Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE, #[wars/0074]
  #'ln1gk1snl/1r1s2g2/p1pppp1pp/1p4p2/9/2P4P1/PPSPPPP1P/2G4R1/LN2KGSNL w Bb 12 6h7g': Opening.BISHOP_EXCHANGE, #[wars/0030]
  #'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13 2b3c': Opening.BISHOP_EXCHANGE, #[EveEnfc-Jv8]
  #'ln1gk2nl/1r1s2g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/2G2S1R1/LN2KG1NL b Bb 17 2b3c': Opening.BISHOP_EXCHANGE, #[vE-7Y9XLfgs]
  #'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15 2b3c': Opening.BISHOP_EXCHANGE, #[SPSX76u6-vA]
  'lnsgkgsnl/1r5b1/ppppp1ppp/5p3/9/2P6/PP1PPPPPP/1B5R1/LNSGKGSNL b - 3 4c4d' : Opening.PACMAN, #[wars/0171]
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/2P6/PPNPPPPPP/1B5R1/L1SGKGSNL w - 4 8i7g' : Opening.DEMON_KILLER,
  'lnsgkgsnl/1r5b1/pppppp1pp/6p2/9/1PP6/P2PPPPPP/1B5R1/LNSGKGSNL w - 4 8g8f' : Opening.BISHOP_PAWN_STRATEGY,
})

#'ln1gkgsnl/1r1s3b1/p1pppp1pp/6p2/1p2P4/2P6/PPBP1PPPP/4R4/LNSGKGSNL w - 10': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/6p2/4p4/2P4P1/PP1PPPP1P/1B2GS1R1/LNSGK2NL b - 9': Opening.GOKIGEN_CENTRAL_ROOK,
#'ln1gkgsnl/1r1s3b1/p1pppp1pp/1p4p2/4P4/2P6/PP1P1PPPP/1B2R4/LNSGKGSNL w - 8': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgkgsnl/4r2b1/pppp1p1pp/4p1p2/7P1/2P6/PP1PPPP1P/1B5R1/LNSGKGSNL b - 7': Opening.GOKIGEN_CENTRAL_ROOK,
#'lnsgk1snl/1r4g2/p1pppp1pp/6p2/1p5P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL w Bb 12': Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/1p4p2/7P1/2P6/PPSPPPP1P/7R1/LN1GKGSNL b Bb 13' : Opening.BISHOP_EXCHANGE,
#'lnsgk2nl/1r4g2/p1ppppspp/6p2/1p5P1/2P6/PPSPPPP1P/5S1R1/LN1GKG1NL b Bb 15': Opening.BISHOP_EXCHANGE, #[wars/0017]

def _king_pos(f, t):
  return ('K', ','.join(f'{i}7,{i}8,{i}9' for i in range(f, t)))

_LEFT_KING = _king_pos(5, 10)
_RIGHT_KING = _king_pos(1, 6)

_RECOGNIZER = Recognizer([
  ([('K', '48'), ('G', '58'), ('S', '47'), ('N', '37'), ('L', '19'), ('R', '29') ,
    ('P', '46'), ('P', '36'), ('P', '56,57'), ('P', '25,26'), ('P', '16,17'), ('P', '76')], Opening.RIGHT_HAND_KING),
  ([('S', '27'), ('to', '27'), ('P', '25,26'), ('B', '88'), ('R', '28'), ('P', '76,77'), ('G', '69,78')] +
    last_row_pieces('36') + adjacent_pawns(7, 1, 10, [2, 7]), Opening.PRIMITIVE_CLIMBING_SILVER),
  ([('S', '37'), ('to', '37'), ('P', '25,26'), ('B', '88'), ('R', '28'), ('P', '36'), ('P', '76,77'), ('G', '78')] +
    last_row_pieces('36') + adjacent_pawns(7, 1, 10, [2, 3, 7]), Opening.PRIMITIVE_CLIMBING_SILVER),
  ([('R', '58'), ('to', '58'), ('P', '55,56'), ('P', '76'), ('B', '77,88')] +
    last_row_pieces('') + adjacent_pawns(7, 2, 9, [5, 7]), Opening.GOKIGEN_CENTRAL_ROOK),
  #([('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85')], Opening.RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '25,26,27,28,29'), ('r','81,82,83,84,85'),
    ('B', 1), ('b', 1), ('P', '36'), ('N', '29,37'), ('G', '48,58'), ('K', '68'),
     ], Opening.BISHOP_EXCHANGE_RECLINING_SILVER),
  ([('to', '56'), ('S', '56'), ('P', '46'), ('P', '67'), ('P', '57'), ('R', '26,28'),
    ('B', 0), ('b', 0), ('P', '36'), ('N', '37'), ('P', '76'), ('G', '78'), ('G', '49'), _LEFT_KING,
     ], Opening.RECLINING_SILVER),
  ([('B', '79'), ('K', '59'), ('S', '78'), ('P', '56'), ('R', '28'), ('!r', '82'),
    ('P', '25,26'), ('P', '96,97'), ('P', '16,17'),
    ('L', '19'), ('L', '99'), ('N', '29'), ('N', '89'), ('S', '39,48'), ('G', '69'), ('G', '58,69')] +
   adjacent_pawns(7, 3, 9, [5]), Opening.IJIMAS_BACK_BISHOP_STRATEGY),
  ([('G', '77'), ('R', '88'), ('P', '76'), ('P', '26,27'), ('to', '88'),
    ('B', 1), ('b', 1), #bishops exchanged
    ('P', '96,97'), ('P', '16,17')] +
    last_row_pieces('6') + adjacent_pawns(7, 3, 9, [7]), Opening.SAKATA_OPPOSING_ROOK),
  ([('S', '77'), ('R', '28'), ('B', 1), ('b', 1), ('P', '76'), ('P', '67'), #('r', '82'),
   ('K', '59'), ('L', '99'), ('L', '19'), ('N', '29'), ('N', '89'), ('from', '68,88'), ('to', '77'), ('G', '78'),
   ('max-gold-moves', 2),
   ], Opening.BISHOP_EXCHANGE),
  ([('S', '26'), ('from', '27'), ('to', '26'), ('P', '25'), ('R', '28'), ('P', '37'),
    ('B', 1), ('b', 1), _LEFT_KING], Opening.BISHOP_EXCHANGE_CLIMBING_SILVER),
  ([('B', '77'), ('from', '88'), ('to', '77'), ('K', '78'), ('G', '49,58,67'),
   ('P', '87'), ('P', '76'), ('P', '66,67'), ('P', '56'), ('S', '48,57'), ('R', '28'), ('!p', '43'), ('r', '22,32,42')] +
   last_row_pieces('2345'), Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE),
  ([('K', '78'), ('B', '88'), ('from', '87'), ('to', '86'), ('R', '28'), ('P', '86'), ('S', '57'), ('G', '58'), ('r', '22,32,42'), ('P', '56'), ('P', '25,26'), ('P', '36,37'), ('P', '96,97'), ('P', '76') ]
   + last_row_pieces('345') + adjacent_pawns(7, 4, 7, [5]), Opening.SWINGING_ROOK_SLOW_GAME_COUNTERMEASURE),
  ([('B', '66'), ('R', '88'), ('to', '88'), ('S', '77'), ('P', '76')] +
    last_row_pieces('7') + adjacent_pawns(7, 2, 9, [7]), Opening.AMAHIKO_OPPOSING_ROOK),
  ([('B', '79'), ('K', '78'), ('S', '57'), ('R', '28'), ('P', '56'), ('P', '25'), ('P', '36,37')] +
    last_row_pieces('357') + adjacent_pawns(7, 4, 9, [5]), Opening.SPEARING_THE_BIRD),
  ([('P', '36'), ('to', '36'), ('R', '68'), ('S', '38'), ('S', '67,78'), ('G', '58,69'), ('B', '77'),
    ('P', '76'), ('P', '66,67'), ('P', '57'), ('P', '87'), ('P', '27'), ('P', '15,16')] +
    last_row_pieces('367'), Opening.FUJII_SYSTEM),
  ([('P', '46'), ('to', '46'), ('R', '68'), ('S', '38'), ('S', '67,78'), ('G', '58,69'), ('B', '77,88'),
    ('P', '76'), ('P', '66,67'), ('P', '57'), ('P', '87'), ('P', '27'), ('P', '15,16')] +
    last_row_pieces('367'), Opening.FUJII_SYSTEM),
  ([('K', '69'), ('G', '78'), ('G', '58'), ('S', '67'), ('S', '47'), ('to', '47'),
    ('P', '76'), ('P', '66'), ('P', '56,57'), ('P', '46'), ('N', '89'), ('L', '99'), ('N', '29,37'), ('L', '19'), ('B', '77,88')], Opening.SILVER_HORNED_SNOW_ROOF),
  ([('P', '75'), ('R', '78'), ('to', '78'), ('from', '28'), ('B', '88'), ('p', '34')] +
   last_row_pieces('') + adjacent_pawns(7, 1, 10, [7]), Opening.QUICK_ISHIDA),
  ([('K', '48'), ('to', '48'), ('R', '78'), ('P', '75'), ('B', '88'), ('r', '82'), ('p', '34'), ('p', '84,85')] +
   last_row_pieces('5') + adjacent_pawns(7, 1, 10, [7]), Opening.MASUDAS_ISHIDA_STYLE),
  ([('R', '76'), ('N', '77'), ('to', '77'), ('P', '66'), ('P', '75'), ('P', '87'), ('B', '88,97'), ('P', '96,97'), ('L', '99'), _RIGHT_KING ], Opening.ISHIDA_STYLE),
  ([('G', '27'), ('to', '27'), ('from', '38'), ('P', '25,26'), ('R', '28'),
    ('N', '29'), ('L', '19'), ('p', '34,35'), _LEFT_KING], Opening.CLIMBING_GOLD), #('P', '37'),
  ([('HORSE', '22'), ('to', '22'), ('from', '88'), ('side', -1), ('R', '28'), ('G', '69,78'), ('P', '76')] +
   adjacent_pawns(7, 3, 7, []) + last_row_pieces('36'), Opening.ONE_TURN_LOSS_BISHOP_EXCHANGE),
  ([('R', '68'), ('to', '68'), ('from', '28'), ('B', 1), ('b', 1), ('S', '77')] +
   last_row_pieces('7') + adjacent_pawns(7, 2, 9, [7]), Opening.LEGHORN_SPECIAL),
  ([('K', '59,69'), ('S', '36'), ('to', '36'), ('from', '27'), ('R', '28'), ('G', '78'), (' ', '25'), (' ', '24'), ('g', '32')] +
   last_row_pieces('356') + adjacent_pawns(7, 3, 7, []), Opening.UFO_SILVER),
  ([ ('R', '78'), ('from', '68'), ('to', '78'), ('P', '75,76'), ('K', '38'), ('B', '88')] +
  last_row_pieces('5') + adjacent_pawns(7, 2, 9, [7]), Opening.FORTH_THIRD_FILE_ROOK_STRATEGY),
  ([ ('R', '88'), ('from', '28'), ('to', '88'), ('S', '77'), ('P', '76')] +
   last_row_pieces('7') + adjacent_pawns(7, 2, 9, [6, 7]), Opening.DIRECT_OPPOSING_ROOK),
  ([('P', '56'), ('to', '56'), ('G', '78'), ('S', '68'), ('S', '48'), ('B', '88'), ('R', '28'), ('P', '25,26,27'), ('r', '82')] +
    adjacent_pawns(7, 3, 9, [5]) + last_row_pieces('367'), Opening.MURATA_SYSTEM), #('p', 0)
  ([('R', '58'), ('to', '58'), ('from', '28'), ('B', '77,88'), ('S', '67,68'), ('P', '76,77'), ('P', '66,67')] + last_row_pieces('7')
   + adjacent_pawns(7, 2, 9, [6, 7]), Opening.HIDE_CHAN_STYLE_CENTRAL_ROOK),
  ([('R', '58'), ('N', '77,89'), ('S', '66'), ('S', '46'), ('P', '23,24,25'), ('P', '56'), ('P', '76')]
   + last_row_pieces('378') + adjacent_pawns(7, 3, 9, [5, 7]), Opening.CRAB_SILVERS),
  ([('S', '37'), ('to', '37'), ('from', '48'), ('K', '69'), ('S', '77'), ('G', '78'), ('G', '49,58,67'), ('R', '28'), ('B', '46,79,88'),
    ('P', '25,26'), ('P', '16,17'), ('P', '96,97'), ('P', '66,67')]
   + last_row_pieces('34567') + adjacent_pawns(6, 3, 8, [4, 6]) + adjacent_pawns(7, 4, 9, [5, 6, 7]), Opening.SILVER37_STRATEGY),
  ([('K', '88'), ('k', '22'),
    ('B', '64'), ('B', 1),
    ('from', '46'), ('to', '64'),
    ('S', '37'), ('s', '73'),
    ('G', '78'), ('g', '32'),
    ('G', '67'), ('g', '43'),
    ('S', '77'), ('s', '33'),
    ('n', '21'), ('n', '81'), ('l', '91'), ('l', '11'),
    ('P', '87'), ('P', '25,26'), ('P', '15,16'), ('P', '96,97'),
    ('p', '23'), ('p', '84,85'), ('p', '13,14'), ('p', '93,94'),
    ('p', '74'), ('p', '54'), ('p', '44'), ('p', '34'), ('p', '63')] +
   last_row_pieces('34567') +
   adjacent_pawns(6, 3, 8, [4]), Opening.WAKI_SYSTEM),
  ([('K', '69'), ('R', '28'), ('B', '68'), ('from', '79'), ('to', '68'), ('S', '77'), ('G', '67'), ('G', '78'),
   ('P', '87'), ('P', '47'), ('P', '25,26,27'), ('P', '16,17'), ('P', '96,97'),
   ('k', '41'), ('r', '82'), ('b', '31'), ('g', '32'), ('g', '52'), ('s', '33'), ('s', '62'),
   ('n', '21'), ('n', '81'), ('l', '11'), ('l', '91'),
   ('p', '34'), ('p', '44'), ('p', '54'), ('p', '74'), ('p', '63'), ('p', '23'),
   ('p', '13,14'), ('p', '93,94'), ('p', '23,24,25')] +
  last_row_pieces('34567') + adjacent_pawns(6, 3, 8, [4]), Opening.MORISHITA_SYSTEM),
  ([('K', '29'), ('from', '38'), ('to', '29'), ('N', '37'), ('G', '39,49'), ('S', '28'), ('P', '76'), ('P', '96,97'), ('P', '87'),
    ('R', '68,78,88')] +
   last_row_pieces('234567'), Opening.SWINGING_ROOK_MILLENIUM),
  ([('R', '58'), ('B', '88'), ('G', '78'), ('P', '55'), ('from', '56'), ('to', '55'), ('S', '57,66,68,79')] +
   last_row_pieces('67') + adjacent_pawns(7, 2, 9, [5]), Opening.PRIMITIVE_CENTRAL_ROOK),
  ([('K', '69'), ('B', '88'), ('G', '78'), ('G', '58'), ('R', '28'), ('S', '47'), ('N', '37'),
    ('S', '66'), ('to', '66'), ('from', '77'), ('P', '25,26'), ('P', '87'), ('P', '16,17'), ('P', '96,97')] +
   last_row_pieces('234567') + adjacent_pawns(6, 3, 8, [6]), Opening.YONENAGA_STYLE_RAPID_ENGAGING_YAGURA),
  ([('K', '78'), ('to', '38'), ('from', '28'), ('B', '88'), ('G', '68,69'), ('G', '58'), ('S', '48'), ('R', '38'),
    ('S', '57'), ('P', '16,17'), ('P', '25'), ('P', '36'), ('P', '47'), ('P', '56'), ('P', '67'), ('P', '76'),
    ('P', '87'), ('P', '96,97')] + last_row_pieces('34567'), Opening.SAGINOMIYA_JOSEKI),
  ([('K', '78'), ('R', '38'), ('to', '38'), ('from', '28'), ('B', '88'), ('S', '68'), ('G', '58'),
    ('S', '57'), ('P', '46,47'), ('P', '25'), ('P', '16,17'), ('P', '96,97')] +
    last_row_pieces('3457') + adjacent_pawns(6, 3, 8, [4,6]), Opening.KATO_STYLE_SLEEVE_ROOK),
  ([('K', '28,38'), ('B', '88'), ('G', '78'), ('R', '68'), ('S', '78,79'), ('P', '16,17'), ('P', '96,97'),
    ('P', '75'), ('P', '65'), ('to', '65'), ('P', '87')] +
   last_row_pieces('356') + adjacent_pawns(7, 2, 6), Opening.TATEISHI_STYLE),
  ([('K', '28,38,48,59'), ('R', '68,78'), ('HORSE', '22'), ('to', '22'), ('from', '88'), ('B', 1)]
   + last_row_pieces('5'), Opening.BISHOP_EXCHANGE_SWINGING_ROOK),
  ([('P', '24'), ('to', '24'), ('B', '88'), ('G', '78'), ('R', '28'),
    ('p', '85'), ('r', '82'), ('s', '31'), ('s', '71,72'), ('g', '61'), ('k', '51'), ('g', '32')
    ] +
    last_row_pieces('6') + adjacent_pawns(7, 1, 10, [2]), Opening.DOUBLE_WING_ATTACK),
  ([('P', '25'), ('S', '38'), ('to', '38'), ('B', '88'), ('G', '78'), ('R', '28'),
    ('p', '85'), ('r', '82'), ('s', '31'), ('s', '71,72'), ('g', '61'), ('k', '51'), ('g', '32'),
    ] +
    last_row_pieces('36') + adjacent_pawns(7, 1, 10, [2]), Opening.DOUBLE_WING_ATTACK),
  ([('K', '68'), ('B', '88'), ('R', '28'), ('S', '37'), ('to', '37'), ('from', '48'), ('P', '36'), ('P', '25'), ('P', '76')] +
   last_row_pieces('35') + adjacent_pawns(7, 1, 10, [2, 3, 7]), Opening.SILVER37_SUPER_RAPID),
  ([('K', '78'), ('B', '88'), ('G', '68,69'), ('G', '58'), ('R', '28'), ('S', '57'), ('S', '26'), ('from', '37'), ('to', '26'), ('P', '25'), ('P', '87'), ('P', '67')] +
   last_row_pieces('34567') + adjacent_pawns(6, 3, 8, [6]), Opening.CLIMBING_SILVER),
  ([('K', '59,69'), ('B', '88'), ('G', '78'), ('S', '27'), ('to', '27'), ('from', '38'), ('R', '28'),
    (' ', '26'), (' ', '25'), (' ', '24'), ('P', 1)] + #('p', '85'), ('r', '82')
   last_row_pieces('3567') + adjacent_pawns(7, 3, 9, [7]), Opening.DOUBLE_WING_ATTACK_CLIMBING_SILVER),
  ([('K', '79'), ('R', '48'), ('to', '48'), ('S', '78'), ('G', '58'), ('B', '66,88'), ('S', '56'), ('N', '29,37'), ('P', '36,37')] +
   adjacent_pawns(6, 2, 5, [3]) + adjacent_pawns(7, 5, 9, [7]) + last_row_pieces('23457'),
   Opening.RIGHT_HAND_FORTH_FILE_ROOK_WITH_LEFT_HAND_MINO),
  ([('K', '68,78'), ('to', '68,78'), ('R', '89'), ('G', '58'), ('G', '38'), ('N', '77'), ('S', '67'), ('S', '57'), ('P', '56'), ('P', '65'), ('P', '76')] +
   adjacent_pawns(7, 2, 9, [5,6,7]) + last_row_pieces('345678'), 'TAKADA'),
  ([('base-pattern', 'TAKADA'), ('B', '66')], Opening.TAKADA_STYLE_LEFT_HAND_KING),
  ([('base-pattern', 'TAKADA'), ('B', 1)], Opening.TAKADA_STYLE_LEFT_HAND_KING),
  ([('K', '59,68,78'), ('R', '28'), ('S', '77'), ('S', '46'), ('to', '46'), ('from', '37'), ('P', '25'), ('P', '36'), ('P', '76'), ('G', '69,78'), ('G', '49,58'), ('B', 1)] +
    last_row_pieces('34567') + adjacent_pawns(7, 4, 9, [7]), Opening.RAPID_ADVANCING_SILVER),
  ([('S', '88'), ('G', '78'), ('B', '77'), ('R', '25'), ('from', '24'), ('to', '25'), ('P', 2)] + last_row_pieces('67') + adjacent_pawns(7, 3, 7), Opening.ROOK85_STRATEGY),
  ([('G', '66'), ('from', '77'), ('to', '66'), ('B', '88'), ('R', '28'), ('P', '76')] +
  last_row_pieces('6') + adjacent_pawns(7, 2, 9, [7]), Opening.KIM_KIM_GOLD),
  ([('K', '69'), ('G', '47'), ('to', '47'), ('from', '58'), ('B', '88'), ('R', '28'), ('N', '29,37'),
    ('P', '25'), ('P', '36'), ('P', '55'), ('P', '67'), ('P', '76'), ('P', '87')] +
   last_row_pieces('234567'), Opening.NAKAHARA_STYLE_RAPID_ENGAGING_YAGURA),
  ([('K', '69'), ('R', '58'), ('to', '58'), ('from', '28'), ('G', '78'), ('B', '88'), ('S', '68,77'), ('S', '47'), ('N', '37'),
    ('P', '67'), ('P', '87')] +
   last_row_pieces('23567') + adjacent_pawns(6, 2, 8, [6]), Opening.YAGURA_CENTRAL_ROOK),
  ([('K', '19'), ('to', '19'), ('from', '28'), ('L', '18'), ('R', '16'), ('P', '15'), ('p', 0)]
   + last_row_pieces('134567') + adjacent_pawns(7, 2, 9), Opening.FIRST_FILE_ROOK_ANAGUMA),
  ([('R', '16'), ('to', '16'), ('from', '18'), ('P', '15'), ('S', '78,79'), ('G', '69,78'), ('p', 0)] +
   last_row_pieces('67') + adjacent_pawns(7, 2, 9), Opening.FIRST_FILE_ROOK),
  ([('K', '48'), ('N', '17'), ('to', '17'), ('R', '78'), ('P', '15'), ('B', '77,88'), ('S', '45,56,67'), ('P', '66'), ('P', '76')] +
   last_row_pieces('257') + adjacent_pawns(7, 2, 9, [6, 7]), Opening.TOMAHAWK),
])

del _LEFT_KING
del _RIGHT_KING
_SWAPPED_LEFT_KING = ('k', ','.join(f'{i}1,{i}2' for i in range(3, 6)))

_RIGHT_HAND_FORTH_FILE_ROOK_RECOGNIZER = Recognizer([
  #recognize before move, so pawn had inverted color and mirrored cell position
  ([('p', '64'), ('P', '66'), _SWAPPED_LEFT_KING, _king_pos(1, 10)], Opening.RIGHT_HAND_FORTH_FILE_ROOK),
])

del _SWAPPED_LEFT_KING

def position_find_opening(pos: PositionForPatternRecognition) -> Optional[Opening]:
  assert isinstance(pos, PositionForPatternRecognition)
  ot = _OPENINGS_D.get(pos)
  if not ot is None:
    if ot == Opening.NONE:
      ot = None
    return ot
  m = pos.last_move
  if not m is None:
    ot = _OPENINGS_POS_AND_MOVE_D.get(pos, m)
    if not ot is None:
      return ot
  return _RECOGNIZER.find(pos)

def _position_update_set_of_openings(rr: RecognizerResult, pos: PositionForPatternRecognition) -> Opening:
  ot = position_find_opening(pos)
  if ot is None:
    return None
  s = rr.get_set(-pos.side_to_move)
  if ot in s:
    return None
  s.add(ot, pos.move_no - 1)
  return ot

_BEFORE_ROOK_OPENING_S = set([Opening.URESINO_STYLE, Opening.PRIMITIVE_CLIMBING_SILVER])
_BEFORE_FORTH_FILE_ROOK_S = set([Opening.URESINO_STYLE, Opening.PRIMITIVE_CLIMBING_SILVER, Opening.QUICK_ISHIDA])

def _almost_empty(s) -> bool:
  return s.issubset(_BEFORE_ROOK_OPENING_S)

def _update_set_of_oppenings_by_rooks(rr: RecognizerResult, pos: PositionForPatternRecognition, col: int):
  s = rr.get_set(pos.side_to_move)
  if col < 5:
    if (pos.move_no <= 20) and (Opening.SWINGING_ROOK in rr.get_set(-pos.side_to_move)):
      s.add(Opening.DOUBLE_SWINGING_ROOK, pos.move_no)
      return
  if col == 2:
    if _almost_empty(s):
      s.add(Opening.OPPOSING_ROOK, pos.move_no)
    s.add(Opening.SWINGING_ROOK, pos.move_no)
  elif col == 3:
    if pos.move_no == 1:
      s.add(Opening.ROOK78_STRATEGY, pos.move_no)
    elif pos.move_no == 2:
      s.add(Opening.ROOK32_STRATEGY, pos.move_no)
    elif _almost_empty(s):
      s.add(Opening.THIRD_FILE_ROOK, pos.move_no)
    s.add(Opening.SWINGING_ROOK, pos.move_no)
  elif col == 4:
    if s.issubset(_BEFORE_FORTH_FILE_ROOK_S):
      s.add(Opening.FORTH_FILE_ROOK, pos.move_no)
    s.add(Opening.SWINGING_ROOK, pos.move_no)
  elif col == 5:
    s.add(Opening.SWINGING_ROOK, pos.move_no)
  elif col == 6:
    if _almost_empty(s) and _RIGHT_HAND_FORTH_FILE_ROOK_RECOGNIZER.find(pos) == Opening.RIGHT_HAND_FORTH_FILE_ROOK:
      s.add(Opening.RIGHT_HAND_FORTH_FILE_ROOK, pos.move_no)
  elif col == 7:
    #TODO: use pattern matching for sleeve rook
    if _almost_empty(s) and pos.move_no <= 5:
      s.add(Opening.SLEEVE_ROOK, pos.move_no)

def _remove_redundant(s):
  s.discard(Opening.SWINGING_ROOK)
  if Opening.SAKATA_OPPOSING_ROOK in s:
    s.discard(Opening.BISHOP_EXCHANGE)
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.AMAHIKO_OPPOSING_ROOK in s:
    s.discard(Opening.OPPOSING_ROOK)
  if Opening.PRIMITIVE_CLIMBING_SILVER in s:
    s.discard(Opening.RIGHT_HAND_FORTH_FILE_ROOK)
  if Opening.LEGHORN_SPECIAL in s:
    s.discard(Opening.FORTH_FILE_ROOK)
  if Opening.QUICK_ISHIDA in s:
    s.discard(Opening.THIRD_FILE_ROOK)
  if not Opening.BISHOP_EXCHANGE in s:
    s.discard(Opening.BISHOP_EXCHANGE_RECLINING_SILVER)

_GOTE_URESINO_FIRST_MOVE = kifu.move_parse('４二銀(31)', -1, None)

def game_find_openings(g: Game, max_hands: int = 60) -> RecognizerResult:
  assert g.start_pos is None
  _RECOGNIZER.reorder()
  rr = RecognizerResult()
  pos = PositionForPatternRecognition()
  try:
    if g.moves[1] == _GOTE_URESINO_FIRST_MOVE:
      s = rr.get_set(-1)
      s.add(Opening.URESINO_STYLE, 2)
  except IndexError:
    pass
  for m in g.moves[:max_hands]:
    col = pos.first_rook_move_rank(m)
    if not col is None:
      _update_set_of_oppenings_by_rooks(rr, pos, col)
    pos.do_move(m)
    _position_update_set_of_openings(rr, pos)
  _remove_redundant(rr.get_set(1))
  _remove_redundant(rr.get_set(-1))
  return rr

"""
class Opening:
  def __init__(self, usi_moves: str, jp_name: str, en_name: str, url: str):
    self.usi_moves = usi_moves
    self.jp_name = jp_name
    self.en_name = en_name
    self.url = url

OPENINGS = [
  Opening('7g7f 3c3d 8h2b+ 3a2b B*4e',
    '筋違角', 'Wrong Diagonal Bishop', 'https://en.wikipedia.org/wiki/Wrong_Diagonal_Bishop'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h 8f7f',
   '相横歩取り','Double Side Pawn Capture', 'https://en.wikipedia.org/wiki/Double_Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*2h 3i2h B*4e',
   '横歩取り☖４五角', 'Side Pawn Capture, Bishop*45', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop*45'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b8h+ 7i8h P*3h',
    '', '3rd File Pawn Drop Option', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d',
    '横歩取り', 'Side Pawn Picker', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2a3c',
    '横歩取り3三桂', 'Side Pawn Capture Knight-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c',
    '横歩取り3三角', 'Side Pawn Capture Bishop-33', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3f 8f8e',
    '', "Chūza's Rook", 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i5h',
    '青野流', 'Aono Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 5i6h',
    '勇気流', 'Yūki Side Pawn', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 8c8d 6i7h 4a3b 2f2e 8d8e 2e2d 2c2d 2h2d 8e8f 8g8f 8b8f 2d3d 2b3c 3d3c+',
    '', 'Takebe Rx33+ variation', 'https://en.wikipedia.org/wiki/Side_Pawn_Capture,_Bishop-33'),
  Opening('7g7f 3c3d 2g2f 4c4d 2f2e 2b3c 3i4h 8b4b 5g5f 9c9d 9g9f 7a7b 5i6h 3a3b 6h7h 5a6b 4i5h 6b7a 3g3f 7a8b 7i6h 4a5b 6h5g',
    '5七銀左急戦', 'Left Silver-57 Rapid Attack', 'https://en.wikipedia.org/wiki/Left_Silver-57_Rapid_Attack'),
  Opening('7g7f 8c8d 5g5f 3c3d 5f5e 5a4b 2h5h 7a6b 5i4h 8d8e 8h7g 7c7d 7i6h 6b7c',
    '超速3七銀', 'Super High Speed Silver-37', 'https://en.wikipedia.org/wiki/Super_High_Speed_Silver-37'),
]
"""
