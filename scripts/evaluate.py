import sys, os
import shlex
import subprocess
import re
from tempfile import NamedTemporaryFile
import pathlib
import shutil


def get_m2score(preds, srcs, refs, keep_gold=False):

    # get the directory of this script
    scripts_dir = pathlib.Path(__file__).parent.resolve()

    with NamedTemporaryFile(mode='r+') as f_src, \
         NamedTemporaryFile(mode='w') as f_src_tok, \
         NamedTemporaryFile(mode='r+') as f_ref, \
         NamedTemporaryFile(mode='w') as f_ref_tok, \
         NamedTemporaryFile(mode='w') as f_gold, \
         NamedTemporaryFile(mode='w') as f_gold_m2, \
         NamedTemporaryFile(mode='r+') as f_pred, \
         NamedTemporaryFile(mode='r+') as f_pred_tok:

        for pred in preds:
            print(pred, file=f_pred)
        for src in srcs:
            print(src, file=f_src)
        for ref in refs:
            print(ref, file=f_ref)

        f_src.seek(0)
        command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
        if run_command(command, std_input=f_src, std_output=f_src_tok) != 0:
            raise Exception("Error while tokenizing src file")

        f_ref.seek(0)
        command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
        if run_command(command, std_input=f_ref, std_output=f_ref_tok) != 0:
            raise Exception("Error while tokenizing ref file")

        f_pred.seek(0)
        command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
        if run_command(command, std_input=f_pred, std_output=f_pred_tok) != 0:
            raise Exception("Error while tokenizing pred file")

        command = f"paste {f_ref_tok.name} {f_src_tok.name}"
        if run_command(command, std_output=f_gold) != 0:
            raise Exception("Error while merging gold ref and src files")

        command = f"python3 {os.path.join(scripts_dir, 'testset_to_m2score.py')} --testset {f_gold.name}"
        if run_command(command, std_output=f_gold_m2) != 0:
            raise Exception("Error while formatting gold reference file")
        if keep_gold:
            gold_fpath = os.path.join(os.getcwd(), 'gold.m2')
            shutil.copyfile(f_gold_m2.name, gold_fpath)
        
        command = f"python2 {os.path.join(scripts_dir, 'm2scorer.py')} {f_pred_tok.name} {f_gold_m2.name}"
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        res = re.findall(r'[^_]\d+\.\d*', stdout.decode())
        p, r, f = float(res[0]), float(res[1]), float(res[2])
        
    return p, r, f


def run_command(command, std_input=None, std_output=None):

    #print("[COMMAND] " + command)
    stdin = subprocess.PIPE
    if std_input:
        stdin = std_input
    stdout = subprocess.PIPE
    if std_output:
        stdout = std_output
    process = subprocess.Popen(shlex.split(command), stdin=stdin, stdout=stdout)
    while True:
        if not std_output:
            output = process.stdout.readline()
            if output:
                print(output.strip().decode())
        if process.poll() is not None:
            break
       
    rc = process.poll()
    return rc
