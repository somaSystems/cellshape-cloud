"""
Vendored and adapted from:
@Author: An Tao
@Contact: ta19@mails.tsinghua.edu.cn
@Time: 2020/3/23 5:39 PM
@License: cellshape_cloud/_vendor/models/LICENSE
"""

import torch


def knn(x, k):
    batch_size = x.size(0)
    num_points = x.size(2)

    inner = -2 * torch.matmul(x.transpose(2, 1), x)
    xx = torch.sum(x**2, dim=1, keepdim=True)
    pairwise_distance = -xx - inner - xx.transpose(2, 1)

    idx = pairwise_distance.topk(k=k, dim=-1)[1]

    if idx.get_device() == -1:
        idx_base = torch.arange(0, batch_size).view(-1, 1, 1) * num_points
    else:
        idx_base = (
            torch.arange(0, batch_size, device=idx.get_device()).view(-1, 1, 1)
            * num_points
        )
    idx = idx + idx_base
    idx = idx.view(-1)

    return idx


def local_cov(pts, idx):
    batch_size = pts.size(0)
    num_points = pts.size(2)
    pts = pts.view(batch_size, -1, num_points)

    _, num_dims, _ = pts.size()

    x = pts.transpose(2, 1).contiguous()
    x = x.view(batch_size * num_points, -1)[idx, :]
    x = x.view(batch_size, num_points, -1, num_dims)

    x = torch.matmul(x[:, :, 0].unsqueeze(3), x[:, :, 1].unsqueeze(2))

    x = x.view(batch_size, num_points, 9).transpose(2, 1)

    x = torch.cat((pts, x), dim=1)

    return x


def local_maxpool(x, idx):
    batch_size = x.size(0)
    num_points = x.size(2)
    x = x.view(batch_size, -1, num_points)

    _, num_dims, _ = x.size()

    x = x.transpose(2, 1).contiguous()
    x = x.view(batch_size * num_points, -1)[idx, :]
    x = x.view(batch_size, num_points, -1, num_dims)
    x, _ = torch.max(x, dim=2)

    return x


def get_graph_feature(x, k=20, idx=None):
    batch_size = x.size(0)
    num_points = x.size(2)
    x = x.view(batch_size, -1, num_points)
    if idx is None:
        idx = knn(x, k=k)

    _, num_dims, _ = x.size()

    x = x.transpose(2, 1).contiguous()
    feature = x.view(batch_size * num_points, -1)[idx, :]
    feature = feature.view(batch_size, num_points, k, num_dims)
    x = x.view(batch_size, num_points, 1, num_dims).repeat(1, 1, k, 1)

    feature = torch.cat((feature - x, x), dim=3).permute(0, 3, 1, 2)

    return feature
