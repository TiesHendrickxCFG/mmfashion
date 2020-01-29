import numpy as np

import torch


class AttrCalculator(object):

    def __init__(self,
                 cfg,
                 tops_type=[3, 5, 10],
                 show_attr_name=False,
                 attr_name_file=None):
        """ create the empty array to count
        true positive(tp), true negative(tn), false positive(fp) and false negative(fn);
        Args:
        cfg(config): testing config
        class_num(int) : number of classes in the dataset
        tops_type(list of int) : default calculate top3, top5 and top10 accuracy
        show_attr_name(bool) : print predicted attribute name, for demo usage
        attr_name_file(str) : file of attribute name, used for mapping attribute index to attribute names
        """
        self.collector = dict()
        self.total = 0  # the number of total predictions
        num_classes = cfg.attribute_num
        for i in tops_type:
            tp, tn, fp, fn = np.zeros(num_classes), np.zeros(
                num_classes), np.zeros(num_classes), np.zeros(num_classes)
            pos = np.zeros(num_classes)
            self.collector['top%s' % str(i)] = dict()
            self.collector['top%s' % str(i)]['tp'] = tp
            self.collector['top%s' % str(i)]['tn'] = tn
            self.collector['top%s' % str(i)]['fp'] = fp
            self.collector['top%s' % str(i)]['fn'] = fn
            self.collector['top%s' % str(i)]['pos'] = pos
        """ precision = true_positive/(true_positive+false_positive)"""
        self.precision = dict()
        """ accuracy = (true_positive+true_negative)/total_precision"""
        self.accuracy = dict()
        """ topn recall rate """
        self.recall = dict()
        self.topn = 50

        self.show_attr_name = show_attr_name
        if self.show_attr_name:
            assert attr_name_file is not None
            # map the index of attribute to attribute name
            self.attr_dict = {}
            attr_names = open(attr_name_file).readlines()
            for i, attr_name in enumerate(attr_names[2:]):
                self.attr_dict[i] = attr_name.split()[0]

    def get_dict(self, fn):
        rf = open(fn).readlines()
        dic = dict()
        for i, line in enumerate(rf):
            id_num = int(line.strip('\n'))
            dic[i] = id_num

        return dic

    def collect(self, indexes, target, top):
        for i, t in enumerate(target):
            if t == 1:
                if i in indexes:
                    top['pos'][i] += 1
                    top['tp'][i] += 1
                else:
                    top['fn'][i] += 1
            if t == 0:
                if i in indexes:
                    top['pos'][i] += 1
                    top['fp'][i] += 1
                else:
                    top['tn'][i] += 1

    def index_to_attribute_name(self, index):
        for pred_i in index:
            pred_attr_name = self.attr_dict[pred_i]
            print(pred_attr_name)

    def collect_result(self, pred, target):
        if isinstance(pred, torch.Tensor):
            data = pred.data.cpu().numpy()
        elif isinstance(pred, np.ndarray):
            data = pred
        else:
            raise TypeError('type {} cannot be calculated.'.format(type(pred)))

        for i in range(pred.size(0)):
            self.total += 1
            indexes = np.argsort(data[i])[::-1]
            idx3, idx5, idx10 = indexes[:3], indexes[:5], indexes[:10]

            self.collect(idx3, target[i], self.collector['top3'])
            self.collect(idx5, target[i], self.collector['top5'])
            self.collect(idx10, target[i], self.collector['top10'])

    def compute_one_recall(self, tp, fn):
        empty = 0
        recall = np.zeros(tp.shape)
        for i, num in enumerate(tp):
            if tp[i] + fn[i] == 0:
                empty += 1
                continue
            else:
                recall[i] = float(tp[i]) / float(tp[i] + fn[i])
        sorted_recall = sorted(recall)[::-1]
        return 100 * sum(sorted_recall[:self.topn]) / min(
            self.topn,
            len(sorted_recall) - empty)

    def compute_recall(self):
        for key, top in self.collector.items():
            self.recall[key] = self.compute_one_recall(top['tp'], top['fn'])

    def compute_one_precision(self, tp, fp, pos):
        empty = 0
        precision = np.zeros(tp.shape)
        for i, num in enumerate(tp):
            if pos[i] == 0:
                empty += 1
                continue
            else:
                precision[i] = float(tp[i]) / float(pos[i])
        sorted_precision = sorted(precision)[::-1]
        return 100 * sum(sorted_precision[:self.topn]) / min(
            self.topn,
            len(sorted_precision) - empty)

    def compute_precision(self):
        for key, top in self.collector.items():
            self.precision[key] = self.compute_one_precision(
                top['tp'], top['fp'], top['pos'])

    def compute_one_accuracy(self, tp, tn):
        accuracy = np.zeros(tp.shape)
        for i, num in enumerate(tp):
            accuracy[i] = float(tp[i] + tn[i]) / float(self.total)
        return 100 * float(np.sum(accuracy)) / len(accuracy)

    def compute_accuracy(self):
        for key, top in self.collector.items():
            self.accuracy[key] = self.compute_one_accuracy(
                top['tp'], top['tn'])

    def show_result(self, batch_idx=None):
        if batch_idx is not None:
            print('\n')
            print('Batch[%d]' % batch_idx)
        else:
            print('Total')

        self.compute_recall()
        print('[Recall] top3 = %.2f, top5 = %.2f, top10 = %.2f' %
              (self.recall['top3'], self.recall['top5'], self.recall['top10']))

        self.compute_accuracy()
        print('[Accuracy] top3 = %.2f, top5 = %.2f, top10 = %.2f' %
              (self.accuracy['top3'], self.accuracy['top5'],
               self.accuracy['top10']))

        print('\n')
