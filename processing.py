from cogroo_interface import Cogroo
import os
import re

# http://www.diveintopython3.net/files.html
# http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html
# https://blogs.msdn.microsoft.com/oldnewthing/20140930-00/?p=43953
# https://pypi.python.org/pypi/chardet

cogroo = Cogroo.Instance()

def clean_text(text):
    pattern1 = re.compile(r'[\x93\x94\x96\x97]')
    pattern2 = re.compile('<.*?>')

    regexes = [pattern1, pattern2]
    pattern_combined = '|'.join(x.pattern for x in regexes)

    clean_text = re.sub(pattern_combined, r'', text)

    return clean_text

def lemmatize_file(s_path, d_path):
    # Arquivo 'problema' usar utf-16le. Nos demais utilizar latin-1
    with open(s_path, encoding='latin-1') as a_file1:
        with open(d_path, 'w', encoding='latin-1') as a_file2:
            for a_line in a_file1:
                clean_line = clean_text(a_line)
                lemma_line = cogroo.lemmatize(clean_line)
                a_file2.write(lemma_line + '\n')

# PRÉ-PROCESSAMENTO: aplica lematização em todos arquivos no folder 'pre-processing'
# obs: a codificação dos caracteres pode variar para cada arquivo o que pode acarretar em erros
def lemmatize_files():
    directory_in = "pre-processing"
    directory_out = "post-processing/output"
    n_file = 0

    for filename in os.listdir(directory_in):
        full_path1 = os.path.join(directory_in, filename)
        full_path2 = directory_out + str(n_file) + '.txt'

        with open(full_path1, encoding='latin-1') as a_file1:
            with open(full_path2, 'w', encoding='latin-1') as a_file2:
                for a_line in a_file1:
                    clean_line = clean_text(a_line)
                    lemma_line = cogroo.lemmatize(clean_line)

                    a_file2.write(lemma_line)
        n_file += 1

# TESTANDO
def extract_info():
    with open("post-processing/esporte-teste.txt", encoding='latin-1') as a_file1:
        for a_line in a_file1:
            a = cogroo.analyze(a_line)
            print(a.sentences[0].tokens[0])
            break

if __name__ == "__main__":
   lemmatize_file("pre-processing/CORPUS DG POLICIA - final.txt", "post-processing/teste.txt")