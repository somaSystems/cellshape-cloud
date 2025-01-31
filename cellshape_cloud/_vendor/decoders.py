"""
Vendored and adapted from:
@Author: An Tao
@Contact: ta19@mails.tsinghua.edu.cn
@Time: 2020/3/23 5:39 PM
@License: cellshape_cloud/_vendor/models/LICENSE
"""
import torch
from torch import nn
import numpy as np
import itertools


class FoldNetDecoder(nn.Module):
    def __init__(self, num_features):
        super(FoldNetDecoder, self).__init__()
        self.m = 2025  # 45 * 45.
        self.meshgrid = [[-3, 3, 45], [-3, 3, 45]]
        self.num_features = num_features
        self.folding1 = nn.Sequential(
            nn.Conv1d(512 + 2, 512, 1),
            nn.ReLU(),
            nn.Conv1d(512, 512, 1),
            nn.ReLU(),
            nn.Conv1d(512, 3, 1),
        )

        self.folding2 = nn.Sequential(
            nn.Conv1d(512 + 3, 512, 1),
            nn.ReLU(),
            nn.Conv1d(512, 512, 1),
            nn.ReLU(),
            nn.Conv1d(512, 3, 1),
        )

        self.lin_features_len = 512
        if self.num_features < self.lin_features_len:
            self.embedding = nn.Linear(
                self.lin_features_len, self.num_features, bias=False
            )
            self.deembedding = nn.Linear(
                self.num_features, self.lin_features_len, bias=False
            )

    def build_grid(self, batch_size):
        x = np.linspace(*self.meshgrid[0])
        y = np.linspace(*self.meshgrid[1])
        points = np.array(list(itertools.product(x, y)))
        points = np.repeat(points[np.newaxis, ...], repeats=batch_size, axis=0)
        points = torch.tensor(points)
        return points.float()

    def forward(self, x):

        if self.num_features < self.lin_features_len:
            x = self.deembedding(x)
            x = x.unsqueeze(1)

        else:
            x = x.unsqueeze(1)
        x = x.transpose(1, 2).repeat(1, 1, self.m)
        points = self.build_grid(x.shape[0]).transpose(1, 2)
        if x.get_device() != -1:
            points = points.cuda(x.get_device())
        cat1 = torch.cat((x, points), dim=1)

        folding_result1 = self.folding1(cat1)
        cat2 = torch.cat((x, folding_result1), dim=1)
        folding_result2 = self.folding2(cat2)
        output = folding_result2.transpose(1, 2)
        return output
