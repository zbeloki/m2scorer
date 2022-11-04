from m2scorer import get_m2score, get_m2score_from_raw, load_m2
import os, sys, pathlib

EXAMPLE_PATH = os.path.join(pathlib.Path(__file__).parent.resolve(), 'example')

def _load_data(pred_fpath, gold_fpath):
    with open(pred_fpath, 'r') as f:
        preds = [ ln.strip() for ln in f.readlines() ]
    gold_data = load_m2(gold_fpath)
    return preds, gold_data

def _evaluate_system(pred_fpath, gold_fpath):
    predictions, gold_data = _load_data(pred_fpath, gold_fpath)
    p, r, f = get_m2score(predictions, gold_data, tokenize=False)
    return p, r, f

def _test_system(pred_fname, gold_fname, ref_p, ref_r, ref_f):
    pred_fpath = os.path.join(EXAMPLE_PATH, pred_fname)
    gold_fpath = os.path.join(EXAMPLE_PATH, gold_fname)
    p, r, f = _evaluate_system(pred_fpath, gold_fpath)
    assert f == ref_f
    assert p == ref_p
    assert r == ref_r

    
# TESTS

def test_system():
    _test_system('system', 'source_gold', 0.8, 0.8, 0.8)
    _test_system('system2', 'source_gold', 0.75, 0.6, 0.7143)


if __name__ == '__main__':

    print("Execute: pytest test.py", file=sys.stderr)
