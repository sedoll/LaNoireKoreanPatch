import os, sys
from wad import wad_read, wad_write
sys.stdout.reconfigure(encoding='utf-8')
GAME = r'D:/SteamLibrary/steamapps/common/L.A.Noire'
PC = GAME + '/final/pc/'
BIG_SOURCES = ['cases.big.pc'] + [f'dlc.dlc{i}.big.pc' for i in (1, 2, 3, 4, 5, 6, 8, 9)]
WAD = PC + 'out.wad.pc'
ROOT_ATB = 'out/attribute/root.atb.pc'
