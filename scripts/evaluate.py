import sys, os
import shlex
import subprocess
import re
from tempfile import NamedTemporaryFile
import pathlib
import shutil
import pdb

from m2scorer.util import smart_open, paragraphs


def get_m2score_from_raw(pred_sents, src_sents, ref_sents, tokenize=True, keep_gold=False):

    # get the directory of this script
    scripts_dir = pathlib.Path(__file__).parent.resolve()

    with NamedTemporaryFile(mode='r+') as f_src, \
         NamedTemporaryFile(mode='w') as f_src_tok, \
         NamedTemporaryFile(mode='r+') as f_ref, \
         NamedTemporaryFile(mode='w') as f_ref_tok, \
         NamedTemporaryFile(mode='w') as f_gold, \
         NamedTemporaryFile(mode='w') as f_gold_m2:

        for src in src_sents:
            print(src, file=f_src)
        f_src.flush()
        for ref in ref_sents:
            print(ref, file=f_ref)
        f_ref.flush()

        if tokenize:
            # tokenise src sentences
            f_src.seek(0)
            command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
            if run_command(command, std_input=f_src, std_output=f_src_tok) != 0:
                raise Exception("Error while tokenizing src file")
            # tokenize ref sentences
            f_ref.seek(0)
            command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
            if run_command(command, std_input=f_ref, std_output=f_ref_tok) != 0:
                raise Exception("Error while tokenizing ref file")
        else:
            # don't tokenise
            f_src_tok = f_src
            f_ref_tok = f_ref

        command = f"paste {f_ref_tok.name} {f_src_tok.name}"
        if run_command(command, std_output=f_gold) != 0:
            raise Exception("Error while merging gold ref and src files")

        command = f"python3 {os.path.join(scripts_dir, 'testset_to_m2score.py')} --testset {f_gold.name}"
        if run_command(command, std_output=f_gold_m2) != 0:
            raise Exception("Error while formatting gold reference file")

        gold_m2 = load_m2(f_gold_m2.name)

        return get_m2score(pred_sents, gold_m2, tokenize=tokenize, keep_gold=keep_gold)


def get_m2score(pred_sents, gold_data, tokenize=True, keep_gold=False):
    """
    pred_sents: [sent1, sent2, ...]
    gold_data: [(source_sentence, {0: [(2, 3, and), ...], 1: []}), ...]
    tokenize: whether tokenize pred sentences or they're already tokenized
    """

    # get the directory of this script
    scripts_dir = pathlib.Path(__file__).parent.resolve()

    with NamedTemporaryFile(mode='w') as f_gold_m2, \
         NamedTemporaryFile(mode='r+') as f_pred, \
         NamedTemporaryFile(mode='r+') as f_pred_tok:

        # pred -> f_pred
        for pred in pred_sents:
            print(pred, file=f_pred)
        f_pred.flush()

        if tokenize:
            # tokenize pred sentences
            f_pred.seek(0)
            command = f"python2 {os.path.join(scripts_dir, 'Tokenizer.py')}"
            if run_command(command, std_input=f_pred, std_output=f_pred_tok) != 0:
                raise Exception("Error while tokenizing pred file")
        else:
            # don't tokenize
            f_pred_tok = f_pred

        build_m2(gold_data, f_gold_m2)
        if keep_gold:
            gold_fpath = os.path.join(os.getcwd(), 'gold.m2')
            shutil.copyfile(f_gold_m2.name, gold_fpath)

        command = f"python2 {os.path.join(scripts_dir, 'm2scorer.py')} {f_pred_tok.name} {f_gold_m2.name}"
        process = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        res = re.findall(r'[^_]\d+\.\d*', stdout.decode())
        p, r, f = float(res[0]), float(res[1]), float(res[2])
        
    return p, r, f


def build_m2(gold_data, f):

    entries = []
    for sent, edits in gold_data:
        entry_lines = [f"S {sent}"]
        for aid, edits in edits.items():
            if len(edits) == 0:
                ln = f"A -1 -1|||noop|||-NONE-|||-NONE-|||-NONE-|||{aid}"
                entry_lines.append(ln)
            else:
                for edit in edits:
                    text = "||".join(edit[2])
                    ln = f"A {edit[0]} {edit[1]}|||-NONE-|||{text}|||-NONE-|||-NONE-|||{aid}"
                    entry_lines.append(ln)
        entries.append('\n'.join(entry_lines))
    f.write('\n\n'.join(entries)+'\n')
    f.flush()
    

def load_m2(gold_file):
    source_sentences = []
    gold_edits = []
    fgold = smart_open(gold_file, 'r')
    puffer = fgold.read()
    fgold.close()
    for item in paragraphs(puffer.splitlines(True)):
        item = item.splitlines(False)
        sentence = [line[2:].strip() for line in item if line.startswith('S ')]
        assert sentence != []
        annotations = {}
        for line in item[1:]:
            if line.startswith('I ') or line.startswith('S '):
                continue
            assert line.startswith('A ')
            line = line[2:]
            fields = line.split('|||')
            start_offset = int(fields[0].split()[0])
            end_offset = int(fields[0].split()[1])
            etype = fields[1]
            if etype == 'noop':
                start_offset = -1
                end_offset = -1
            corrections =  [c.strip() if c != '-NONE-' else '' for c in fields[2].split('||')]
            # NOTE: start and end are *token* offsets
            original = ' '.join(' '.join(sentence).split()[start_offset:end_offset])
            annotator = int(fields[5])
            if annotator not in annotations.keys():
                annotations[annotator] = []
            annotations[annotator].append((start_offset, end_offset, corrections))
        tok_offset = 0
        for this_sentence in sentence:
            tok_offset += len(this_sentence.split())
            source_sentences.append(this_sentence)
            this_edits = {}
            for annotator, annotation in annotations.items():
                this_edits[annotator] = [edit for edit in annotation if edit[0] <= tok_offset and edit[1] <= tok_offset and edit[0] >= 0 and edit[1] >= 0]
            if len(this_edits) == 0:
                this_edits[0] = []
            gold_edits.append(this_edits)
    return list(zip(source_sentences, gold_edits))


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
