from cogroo_interface import Cogroo
import os
import re
import n_gram
import json
import collections

# http://www.diveintopython3.net/files.html
# http://python-notes.curiousefficiency.org/en/latest/python3/text_file_processing.html
# https://blogs.msdn.microsoft.com/oldnewthing/20140930-00/?p=43953
# https://pypi.python.org/pypi/chardet
# https://stackoverflow.com/questions/9525993/get-consecutive-capitalized-words-using-regex

cogroo = Cogroo.Instance()
n_grams = {}

def jsonDefault(object):
    return object.__dict__

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
    #         b = re.sub(r'\s', '-', a)
    #         words.append(b)
    # Get the rest of the words
    aux = re.findall(pattern2, line)
    
    for a in aux:
        words.append(a)

    return words

def process_text(s_path, d_path, n, category):
    g_classes = ['n', 'v', 'v-inf', 'v-pcp', 'v-ger', 'v-fin', 'adj', 'adv']
    if n > 1:
        g_classes.append('prp')

    n_grams[category] = []
    section = ''
    arr = []
    maps_word_grammar = []
    i = 0
    json_str = '{ "' + category + '":['
    
    with open(s_path, encoding='latin-1') as a_file1:  
        for a_line in a_file1:

            clean_line = clean_text(a_line)
            words = get_list_of_words(clean_line)

            for word in words:
                if word == 'TEXTO':
                    section = re.sub('\n', '', clean_line)
                    continue

                if section == '':
                    continue

                l_word = cogroo.lemmatize(word)
                avaliated_word = cogroo.analyze(l_word)
            
                if avaliated_word.sentences:
                    grammar_class = re.findall(r'#(\w+\-*\w*)', str(avaliated_word.sentences[0].tokens))

                if grammar_class[0] in g_classes:
                    arr.append(l_word)
                    maps_word_grammar.append((l_word, grammar_class[0]))

                    if len(arr) == n:
                        ngram = n_gram.NGram(" ".join(arr), list(maps_word_grammar),  section)
                        arr.pop(0)
                        maps_word_grammar.pop(0)
                        
                        j = json.dumps(ngram, indent=4, default=jsonDefault, ensure_ascii=False)
                        json_str += ', ' + j if i > 0 else j
                        i += 1
        json_str += ']}'

    with open(d_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_str)


def get_ngrams_frequencies(n, category, s_path, k):
    data = json.load(open(s_path))
    ng = []
    for i in data[category]:
        ng.append(i['ngram'])

    counter = collections.Counter(ng)

    return counter.most_common()[:k]
            

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

if __name__ == "__main__":
    # generate_testing_and_training_files('original-files/CORPUS DG POLICIA - final.txt', 'training/train-policia.txt', 'testing/test-policia.txt', 'latin-1')
    # process_text('training/train-policia.txt', 'json/policia.json', 2, 'policia')
    print(get_ngrams_frequencies(2, 'policia', 'json/policia.json', 10))
    # for key, values in n_grams.items():
    #     for value in values:
    #         print(vars(value))
