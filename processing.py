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

def process_text(training_path, testing_path, category, f_encoding):
    g_classes = ['n', 'n-adj', 'v', 'v-inf', 'v-pcp', 'v-ger', 'v-fin', 'adj', 'adv']

    directory_category_info = 'text-info-json/'

    if not os.path.exists(directory_category_info):
        os.makedirs(directory_category_info)
    
    for j in range(1, 3):
        data = {}
        data[category] = {}
        section_words = {}
        journal_body = False

        if j == 1:
            directory_ngrams = 'ngrams-training/'
            path = training_path
            action = 'training'
        else:
            directory_ngrams = 'ngrams-testing/'
            path = testing_path
            action = 'testing'

        with open(path, encoding=f_encoding) as a_file1:  
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

        info_path = directory_category_info + category.lower() + '-' + action + '.json'
        with open(info_path, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)

        if not os.path.exists(directory_ngrams):
            os.makedirs(directory_ngrams)

        # Create ngram json files
        for i in range(1, 4):
            d_path = directory_ngrams + category.lower() + '-ngram' + str(i) + '.json'
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
def get_bag_of_words(ngrams_path, n, bow_size):
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
            
    bow = collections.Counter(words).most_common(bow_size)
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(bow)

    return bow, categories
        
# Attributes:
#   n: ngram
#   filename_training: weka training file name
#   filename_testing: weka testing file name
#   f_encoding: files encoding
#   bow_size: bag of words size
# Generates weka files for testing and training
# The weka file is generated based on the ngrams files located in "ngrams-training" and "ngrams_testing" directories
# The "n" attribute specifies wich ngrams files should be read. It reads files from all categories with ngram equals to "n"     
def generate_arff_file(n, filename_training, filename_testing, f_encoding, bow_size):

    directory_ngram_training = 'ngrams-training/'
    directory_ngram_testing = 'ngrams-testing/'

    directory_weka_training = 'weka-training/'
    directory_weka_testing = 'weka-testing/'

    # Get BoW
    bow, categories = get_bag_of_words(directory_ngram_training, n, bow_size)

    # Create weka training and testing directories if they don't exist
    if not os.path.exists(directory_weka_training):
        os.makedirs(directory_weka_training)
    
    if not os.path.exists(directory_weka_testing):
        os.makedirs(directory_weka_testing)

    # First iteration generates weka training file. Second iteration generates weka testing file
    for index in range(1, 3):
        if index == 1:
            directory = directory_weka_training
            directory_ngrams = directory_ngram_training
            f_name = filename_training
        else:
            directory = directory_weka_testing
            directory_ngrams = directory_ngram_testing
            f_name = filename_testing

        with open(directory + f_name + '.arff', 'w', encoding=f_encoding) as a_file2:
            a_file2.write("@RELATION PALAVRAS\n\n")

            for row in bow:
                if n > 1:
                    a_file2.write("@ATTRIBUTE " + row[0].replace(" ", "_") + " INTEGER\n")
                else:
                    a_file2.write("@ATTRIBUTE " + row[0] + " INTEGER\n")
            
            str_categories = ''
            i = 0
            for c in categories:
                str_categories += c if i == 0 else ', ' + c
                i += 1

            a_file2.write("@ATTRIBUTE class" + "{" + str_categories + "}" + "\n\n")
            a_file2.write("@DATA\n")

            for filename in os.listdir(directory_ngrams):
                aux = filename.split(".")
                n_ngram = aux[-2][-1]

                if n_ngram == str(n):
                    path = os.path.join(directory_ngrams, filename)
                    data = json.load(open(path))

                    category = list(data.keys())[0]

                    for key, section in data[category].items():
                        for att in bow:
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
    # generate_testing_and_training_files('original-files/CORPUS DG ESPACO DO TRABALHADOR - final.txt', 'training/train-trabalhador.txt', 'testing/test-trabalhador.txt', 'latin-1')
    # process_text('training/train-trabalhador.txt','testing/test-trabalhador.txt', 'Trabalhador', 'latin-1')
    generate_arff_file(1, 'policia_esporte_problema_trabalhador-ngram1-training', 'policia_esporte_problema_trabalhador-ngram1-testing', 'latin-1', 50)