from cogroo_interface import Cogroo
import os
import re

# http://www.diveintopython3.net/files.html
# http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html
# https://blogs.msdn.microsoft.com/oldnewthing/20140930-00/?p=43953
# https://pypi.python.org/pypi/chardet
# https://stackoverflow.com/questions/9525993/get-consecutive-capitalized-words-using-regex

cogroo = Cogroo.Instance()
lemmatized_words = []
grammar_info = {}

def clean_text(text):
    pattern1 = re.compile(r'[\x93\x94\x96\x97]')
    pattern2 = re.compile('<.*?>')

    regexes = [pattern1, pattern2]
    pattern_combined = '|'.join(x.pattern for x in regexes)

    clean_text = re.sub(pattern_combined, r'', text)

    return clean_text

# Tokenize and Normalize
def get_list_of_words(line):
    pattern1 = re.compile("([A-Z][a-zÀ-ÿ]+(?=\s[A-Z])(?:\s[A-Z][a-zÀ-ÿ]+)+)")
    pattern2 = re.compile("\w+")

    words = []

    # Unify with underline a sequence of words that start with Capital Letter
    # if pattern1.match(line):
    #     aux = re.findall(pattern1, line)
        
    #     for a in aux:
    #         line = line.replace(a, '')
    #         b = re.sub(r'\s', '_', a)
    #         words.append(b)

    # Get the rest of the words
    aux = re.findall(pattern2, line)
    
    for a in aux:
        words.append(a)

    return words

def process_text(s_path, n):
    g_classes = ('n', 'v', 'v-inf', 'v-pcp', 'v-ger', 'v-fin', 'adj', 'adv')
    if n > 1:
        g_classes.append('prp')
    
    with open(s_path, encoding='latin-1') as a_file1:  
        for a_line in a_file1:
            clean_line = clean_text(a_line)
            words = get_list_of_words(a_line)
            
            for word in words:
                l_word = cogroo.lemmatize(word)
                avaliated_word = cogroo.analyze(l_word)

                if avaliated_word.sentences:
                    grammar_class = re.findall(r'#(\w+\-*\w*)', str(avaliated_word.sentences[0].tokens))

                if grammar_class[0] in g_classes:
                    grammar_info[l_word] = grammar_class[0]
                
                lemmatized_words.append(l_word)
                
def generate_testing_and_training_files(s_path, d1_path, d2_path, f_encoding):
    n_texts = 0
    pattern = re.compile("TEXTO")

    with open(s_path, encoding=f_encoding) as a_file1:
        for a_line in a_file1:
            if pattern.match(a_line):
                n_texts += 1
    
    aux = 0
    flag_training = True
    n_training_texts = (n_texts * 80) / 100
    n_testing_texts = n_texts - n_training_texts

    with open(s_path, encoding=f_encoding) as a_file1:
        with open(d1_path, 'w', encoding=f_encoding) as a_file2:
            with open(d2_path, 'w', encoding=f_encoding) as a_file3:
                for a_line in a_file1:
                    
                    if flag_training:     
                        if pattern.match(a_line):
                            aux += 1
                            if  aux > n_training_texts:
                                first_testing_text = a_line
                                flag_training = False
                            else:
                                a_file2.write(a_line + '\n')
                        else:
                            a_file2.write(a_line + '\n')
                    else:
                        if aux == (n_training_texts + 1):
                            a_file3.write(first_testing_text + '\n')
                            aux += 1

                        a_file3.write(a_line + '\n')


# PRÉ-PROCESSAMENTO: aplica lematização em todos arquivos no folder 'pre-processing'
# obs: a codificação dos caracteres pode variar para cada arquivo o que pode acarretar em erros
# def lemmatize_files():
#     directory_in = "pre-processing"
#     directory_out = "post-processing/output"
#     n_file = 0

#     for filename in os.listdir(directory_in):
#         full_path1 = os.path.join(directory_in, filename)
#         full_path2 = directory_out + str(n_file) + '.txt'

#         with open(full_path1, encoding='latin-1') as a_file1:
#             with open(full_path2, 'w', encoding='latin-1') as a_file2:
#                 for a_line in a_file1:
#                     clean_line = clean_text(a_line)
#                     lemma_line = cogroo.lemmatize(clean_line)

#                     a_file2.write(lemma_line)
#         n_file += 1

if __name__ == "__main__":
    # generate_testing_and_training_files('original-files/CORPUS DG POLICIA - final.txt', 'training/train-policia.txt', 'testing/test-policia.txt', 'latin-1')
    process_text('training/train-policia.txt', 1)
    
    # print(grammar_info)