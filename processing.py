from cogroo_interface import Cogroo
import os
import re
import json
import collections
import unidecode
import sys
import pprint


cogroo = Cogroo.Instance()
n_grams = {}

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

# file_type: 'testing' or 'training'
def process_text(s_path, file_type, category):
    g_classes = ['n', 'n-adj', 'v', 'v-inf', 'v-pcp', 'v-ger', 'v-fin', 'adj', 'adv']

    data = {}
    data[category] = {}
    section_words = {}
    journal_body = False

    directory = 'json/'
    
    with open(s_path, encoding='latin-1') as a_file1:  
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
        json.dump(data, json_file, indent=4)

    directory = 'ngrams-' + file_type  + '/'

    if not os.path.exists(directory):
        os.makedirs(directory)

    for i in range(1, 4):
        d_path = directory + category.lower() + '-ngram' + str(i) + '.json'
        ngram_json = {}
        ngram_json[category] = {}

        for key, section in data[category].items():
            aux = 0
            arr = []
            ngram_json[category][key] = []

            for word_info in section:

                word = word_info.split(":")[0]
                arr.append(word)

                if len(arr) == i:
                    ngram = " ".join(arr)
                    ngram_json[category][key].append(ngram)
                    arr.pop(0)

        with open(d_path, 'w', encoding='utf-8') as json_file:
            json.dump(ngram_json, json_file, indent=4)

# n: ngram 1, 2 or 3
def get_bag_of_words(ngrams_path, n):
    words = {}
    category = ''
    bow = {}
    categories = []

    for filename in os.listdir(ngrams_path):
        aux = filename.split(".")
        n_ngram = aux[-2][-1]

        if n_ngram == str(n):
            path = os.path.join(ngrams_path, filename)
            data = json.load(open(path))

            category = list(data.keys())[0]
            categories.append(category)
            words = {}

            for key, section in data[category].items():
                for word in section:
                    if word in words:
                        words[word] += 1
                    else:
                        words[word] = 1
            
    bow = collections.Counter(words).most_common(10)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(bow)

    return bow, categories
        
# n: ngram 1, 2 or 3
# file_type: 'testing' or 'training'          
def generate_arff_file(n, file_type, f_encoding):
    ngrams_path = 'ngrams-' + file_type + '/'

    allRows, categories = get_bag_of_words(ngrams_path, n)

    directory = 'weka-' + file_type + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + 'result.arff', 'w', encoding=f_encoding) as a_file2:
        a_file2.write("@RELATION PALAVRAS\n\n")

        for row in allRows:
            a_file2.write("@ATTRIBUTE " + row[0] + " INTEGER\n")
        
        str_categories = ''
        i = 0
        for c in categories:
            str_categories += c if i == 0 else ', ' + c
            i += 1

        a_file2.write("@ATTRIBUTE class" + "{" + str_categories + "}" + "\n\n")
        a_file2.write("@DATA\n")

        for filename in os.listdir(ngrams_path):
            aux = filename.split(".")
            n_ngram = aux[-2][-1]

            if n_ngram == str(n):
                path = os.path.join(ngrams_path, filename)
                data = json.load(open(path))

                category = list(data.keys())[0]

                for key, section in data[category].items():
                    for att in allRows:
                        flag = 0
                        for ngram in section:
                            if att[0] == ngram:
                                flag = 1
                                break
                        if flag == 1:
                            a_file2.write("1" + ",")
                        else:
                            a_file2.write("0" + ",")           
                    a_file2.write(category + "\n")
            


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
    # generate_testing_and_training_files('original-files/CORPUS DG ESPORTES - final.txt', 'training/train-esporte.txt', 'testing/test-esporte.txt', 'latin-1')
    process_text('testing/test-policia.txt', 'testing', 'Policia')
    generate_arff_file(1, 'testing', 'latin-1')