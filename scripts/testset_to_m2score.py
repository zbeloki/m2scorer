import argparse
from collections import namedtuple
import sys
import pdb

PairTokenized = namedtuple('PairTokenized', 'orig, error')

def main():
    pairs = []
    
    with open(args.testset, 'r') as f:
        for ln in f.readlines():
            cols = ln.split('\t')
            orig_toks = cols[0].strip().split()
            error_toks = cols[1].strip().split()
            pairs.append(PairTokenized(orig_toks, error_toks))
        
    for pair in pairs:
        try:
            diffs = get_diff(pair.error, pair.orig)
            print_pair(pair.error, diffs)
        except Exception as e:
            print(str(e), file=sys.stderr)
        
            
Diff = namedtuple('Diff', 'offset, to, newform')

def get_diff(toks1, toks2, i1 = 0):
    if not toks1 or not toks2:
        diffs = []
        if not toks1:
            for tok in toks2:
                diffs.append(Diff(i1, i1, tok))
        else:  # not toks2
            for j, tok in enumerate(toks1):
                diffs.append(Diff(j+i1, j+i1+1, '-NONE-'))
        return diffs
    elif toks1[0] == toks2[0]:
        return get_diff(toks1[1:], toks2[1:], i1+1)
    else:
        next_i1 = None
        next_i2 = None
        for j in range(max(len(toks1), len(toks2))):
            if next_i1 is not None:
                break
            if len(toks1) > j:
                for j2 in range(min(j+1, len(toks2))):
                    if toks1[j] == toks2[j2]:
                        next_i1 = j
                        next_i2 = j2
                        break
            if len(toks2) > j:
                for j1 in range(min(j+1, len(toks1))):
                    if toks1[j1] == toks2[j]:
                        next_i1 = j1
                        next_i2 = j
                        break
        if next_i1 is None:
            next_i1 = len(toks1)
            next_i2 = len(toks2)
            
        diffs = []
        min_next = min(next_i1, next_i2)
        for j in range(min_next):
            diffs.append(Diff(j+i1, j+i1+1, toks2[j]))
        for j1 in range(min_next, next_i1):
            diffs.append(Diff(j1+i1, j1+i1+1, '-NONE-'))
        for j2 in range(min_next, next_i2):
            diffs.append(Diff(i1, i1, toks2[j2]))
            
        return diffs + get_diff(toks1[next_i1:], toks2[next_i2:], i1+next_i1)
        

def print_pair(sent, diffs):
    print("S {}".format(' '.join(sent)))
    for diff in diffs:
        print("A {} {}|||-NONE-|||{}|||-NONE-|||-NONE-|||0".format(diff.offset, diff.to, diff.newform))
    print()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test-seta m2score tresnaren formatura bihurtzen du, ebaluazioa egiteko.")
    parser.add_argument("--testset", required=True, help='testseta TSV formatuan, zutabeak: orig_sent - error_sent')
    args = parser.parse_args()
    
    main()
