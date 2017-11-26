from cogroo_interface import Cogroo
import os
import re
import n_gram
import json
import collections
import unidecode
import sys


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
    pattern2 = re.compile("\w+")

    words = []

    # Get the rest of the words
    aux = re.findall(pattern2, line)
    
    for a in aux:
        words.append(a)

    return words

def process_text(s_path, category):
    g_classes = ['n', 'n-adj', 'v', 'v-inf', 'v-pcp', 'v-ger', 'v-fin', 'adj', 'adv']

    data = {}
    data[category] = {}
    section_words = {}
    journal_body = False

    directory = 'json/'
    
    with open(s_path, encoding='utf-16le') as a_file1:  
        for a_line in a_file1:
            clean_line = clean_text(a_line)

            split_line = clean_line.split(" ")
                
            if split_line[0] == 'TEXTO':
                if journal_body:
                    if section_number in section_words:
                        data[category][section_number] = section_words[section_number]

                journal_body = True
                section_number = re.sub('\n', '', split_line[1])
                section_words[section_number] = []
                continue

            if journal_body:
                words = get_list_of_words(clean_line)

                for word in words:

                    l_word = cogroo.lemmatize(word)
                    avaliated_word = cogroo.analyze(l_word)
                
                    if avaliated_word.sentences:
                        grammar_class = re.findall(r'#(\w+\-*\w*)', str(avaliated_word.sentences[0].tokens))

                    if grammar_class[0] in g_classes:
                        section_words[section_number].append(unidecode.unidecode(l_word) + ":" + grammar_class[0])

    info_path = directory + category.lower() + '.json'
    with open(info_path, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, sort_keys=True, indent=4)

    for i in range(1, 4):
        d_path = directory + category.lower() + '-ngram' + str(i) + '.txt'
        
        with open(d_path, 'w', encoding='utf-8') as txt_file:
            for k, section in data[category].items():
                aux = 0
                arr = []
                for word_info in section:
                    word = word_info.split(":")[0]
                    arr.append(word)

                    if len(arr) == i:
                        ngram = " ".join(arr)
                        txt_file.write(ngram + '\n')
                        arr.pop(0)


def get_ngrams_frequencies(s_path, source_path, origin, f_encoding):
    
    counts = {}

    for file in os.listdir(s_path):
        file = os.path.join(s_path, file)
        with open(file, encoding=f_encoding) as a_file:
            for word in a_file:
                if word not in counts:
                    counts[word] = 0
                counts[word] += 1

    word_counts = collections.Counter(counts)
    with open(source_path, 'w', encoding=f_encoding) as a_file2:
        for word, count in sorted(word_counts.items()):
            a_file2.write(origin + ";" + str(count) + ";" + word)

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
    #generate_testing_and_training_files('original-files/CORPUS DG O QUE HA DE NOVO - final.txt', 'training/train-novidades.txt', 'testing/test-novidades.txt', 'utf-16le')
    #process_text('training/train-novidades.txt', 'Novidades')
    print(get_ngrams_frequencies('json/trabalhador', 'json/trabalhador/trabalhador-frequencia.txt', 'trabalhador', 'latin-1'))
