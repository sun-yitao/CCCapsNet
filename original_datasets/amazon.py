import os
import sys

import numpy as np
import pandas as pd
from torchnlp.datasets.dataset import Dataset
from torchnlp.download import download_file_maybe_extract

from .data_utils import text_preprocess


def amazon_dataset(directory='data/', train=False, test=False, check_files=['readme.txt'],
                   # amazon_review_full, amazon_review_polarity
                   urls=['https://drive.google.com/uc?export=download&id=1ps9Sh8i9i-1JId-37InvUbk0t4stxh6L',
                         'https://drive.google.com/uc?export=download&id=1Qv9vdBf2LfbQsfcKfMsHAEuSsPCWYUk_'],
                   fine_grained=False):
    """
    Load the Amazon Review Full Score or Amazon Review Polaridy dataset (Version 3).

    The Amazon reviews full score dataset is constructed by randomly taking 600,000 training samples and
    130,000 testing samples for each review score from 1 to 5. In total there are 3,000,000 trainig samples
    and 650,000 testing samples.
    The Amazon reviews polarity dataset is constructed by taking review score 1 and 2 as negative, and 4 and
    5 as positive. For each polarity 1,800,000 training samples and 200,000 testing samples are take randomly.
    In total there are 3,600,000 trainig samples and 400,000 testing samples. Negative polarity is class 1,
    and positive class 2.

    **Reference:** http://jmcauley.ucsd.edu/data/amazon/

    Args:
        directory (str, optional): Directory to cache the dataset.
        train (bool, optional): If to load the training split of the dataset.
        test (bool, optional): If to load the test split of the dataset.
        check_files (str, optional): Check if these files exist, then this download was successful.
        urls (str, optional): URLs to download.
        fine_grained (bool, optional): Whether to use 5-class instead of 2-class labeling. Which means using
        amazon_review_full dataset instead of amazon_review_polarity dataset

    Returns:
        :class:`tuple` of :class:`torchnlp.datasets.Dataset`: Tuple with the training dataset and
        test dataset in order if their respective boolean argument is true.
    """
    if fine_grained:
        extracted_name, url = 'amazon_review_full', urls[0]
    else:
        extracted_name, url = 'amazon_review_polarity', urls[1]
    for i in range(len(check_files)):
        check_files[i] = os.path.join(extracted_name, check_files[i])
    download_file_maybe_extract(url=url, directory=directory, filename=extracted_name + '.tar.gz',
                                check_files=check_files)

    ret = []
    splits = [file_name for (requested, file_name) in [(train, 'train.csv'), (test, 'test.csv')] if requested]
    for file_name in splits:
        csv_file = np.array(pd.read_csv(os.path.join(directory, extracted_name, file_name), header=None)).tolist()
        examples = []
        text_min_length = sys.maxsize
        text_max_length = 0
        for data in csv_file:
            label, title, description = str(data[0]), data[1], data[2]
            if (not isinstance(title, str)) and (not isinstance(description, str)):
                continue
            else:
                if isinstance(title, str) and (not isinstance(description, str)):
                    text = title
                elif isinstance(description, str) and (not isinstance(title, str)):
                    text = description
                else:
                    text = title + ' ' + description
                text = text_preprocess(text)
                if len(text.split()) == 0:
                    continue
                else:
                    if len(text.split()) > text_max_length:
                        text_max_length = len(text.split())
                    if len(text.split()) < text_min_length:
                        text_min_length = len(text.split())
            examples.append({'label': label, 'text': text})
        ret.append(Dataset(examples))
        print('text_min_length:' + str(text_min_length))
        print('text_max_length:' + str(text_max_length))

    if fine_grained:
        train_file, test_file = 'data/amazon_fine_grained_train.txt', 'data/amazon_fine_grained_test.txt'
    else:
        train_file, test_file = 'data/amazon_train.txt', 'data/amazon_test.txt'

    train_f = open(train_file, 'w')
    for train_data in ret[0]:
        train_f.write(train_data['label'] + '\t' + train_data['text'] + '\n')
    train_f.close()
    test_f = open(test_file, 'w')
    for test_data in ret[1]:
        test_f.write(test_data['label'] + '\t' + test_data['text'] + '\n')
    test_f.close()

    if len(ret) == 1:
        return ret[0]
    else:
        return tuple(ret)
