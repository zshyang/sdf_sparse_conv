"""Add field convolution to the first layer of pointnet2.
----ZhangsihaoYang.Jan.10.2021
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from models.pointnet_util import PointNetSetAbstraction
from easydict import EasyDict
from models.layers.field_convolution import FieldConv
from models.layers.sdf_bn import FieldBatchNormalization
from models.layers.sdf_relu import FieldReLU


class Net(nn.Module):
    """The PointNet++ classification model.
    """
    def __init__(self, options: EasyDict):
        """The initialization function.

        Args:
            options: The options to define the model.
        """
        super(Net, self).__init__()

        self.in_channel = 16  # Hard coded here.

        # The first field convolution layer.
        self.field_conv = FieldConv(
            edge_length=0.03, filter_sample_number=64, center_number=16 ** 3, in_channels=1,
            out_channels=self.in_channel,
            feature_is_sdf=True,
        )
        self.fbn = FieldBatchNormalization(16)

        self.num_class = options.model.out_channel

        self.sa1 = PointNetSetAbstraction(
            npoint=512, radius=0.2, nsample=32, in_channel=self.in_channel+3, mlp=[64, 64, 128], group_all=False
        )  # The in channels are increased by 3.

        self.sa1_conv1 = FieldConv(
            edge_length=0.4, filter_sample_number=32, center_number=512, in_channels=16,
            out_channels=64,
            feature_is_sdf=False,
        )
        self.fbn1 = FieldBatchNormalization(64)
        self.relu = FieldReLU()
        self.sa1_conv2 = FieldConv(
            edge_length=0.4, filter_sample_number=32, center_number=512, in_channels=64,
            out_channels=64,
            feature_is_sdf=False,
        )
        self.fbn2 = FieldBatchNormalization(64)
        self.relu = FieldReLU()
        self.sa1_conv3 = FieldConv(
            edge_length=0.4, filter_sample_number=32, center_number=512, in_channels=64,
            out_channels=128,
            feature_is_sdf=False,
        )
        self.fbn3 = FieldBatchNormalization(128)

        self.sa2 = PointNetSetAbstraction(
            npoint=128, radius=0.4, nsample=64, in_channel=128 + 3, mlp=[128, 128, 256], group_all=False
        )
        self.sa2_conv1 = FieldConv(
            edge_length=0.8, filter_sample_number=8, center_number=128, in_channels=128,
            out_channels=128,
            feature_is_sdf=False,
        )
        self.fbn21 = FieldBatchNormalization(128)
        self.sa2_conv2 = FieldConv(
            edge_length=0.8, filter_sample_number=8, center_number=128, in_channels=128,
            out_channels=128,
            feature_is_sdf=False,
        )
        self.fbn22 = FieldBatchNormalization(128)
        self.sa2_conv3 = FieldConv(
            edge_length=0.8, filter_sample_number=8, center_number=128, in_channels=128,
            out_channels=256,
            feature_is_sdf=False,
        )
        self.fbn23 = FieldBatchNormalization(256)

        self.sa3 = PointNetSetAbstraction(
            npoint=None, radius=None, nsample=None, in_channel=256 + 3, mlp=[256, 512, 1024], group_all=True
        )
        self.sa3_conv1 = FieldConv(
            edge_length=2.0, filter_sample_number=8, center_number=128, in_channels=256,
            out_channels=256,
            feature_is_sdf=False,
        )
        self.fbn31 = FieldBatchNormalization(256)
        self.sa3_conv2 = FieldConv(
            edge_length=2.0, filter_sample_number=8, center_number=128, in_channels=256,
            out_channels=512,
            feature_is_sdf=False,
        )
        self.fbn32 = FieldBatchNormalization(512)
        self.sa3_conv3 = FieldConv(
            edge_length=2.0, filter_sample_number=128, center_number=1, in_channels=512,
            out_channels=1024,
            feature_is_sdf=False,
        )
        self.fbn33 = FieldBatchNormalization(1024)

        self.fc1 = nn.Linear(1024, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.drop1 = nn.Dropout(0.4)
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        self.drop2 = nn.Dropout(0.4)
        self.fc3 = nn.Linear(256, self.num_class)

    def forward(self, batch: dict) -> dict:
        """The forward function.

        Args:
            batch: The input batch.
                "xyz_sdf": The input point cloud concatenated with signed distance field.

        Returns:
            The output batch.
        """
        xyz_sdf = batch["xyz_sdf"]

        batch_size, _, _ = xyz_sdf.shape

        field_feature = self.field_conv(xyz_sdf)
        field_feature = self.relu(self.fbn(field_feature))

        field_feature = self.sa1_conv1(field_feature)
        field_feature = self.relu(self.fbn1(field_feature))
        field_feature = self.sa1_conv2(field_feature)
        field_feature = self.relu(self.fbn2(field_feature))
        field_feature = self.sa1_conv3(field_feature)
        field_feature = self.relu(self.fbn3(field_feature))

        # field_feature = field_feature.permute(0, 2, 1)
        #
        # l1_xyz, l1_points = self.sa2(field_feature[:, :3, :], field_feature[:, 3:, :])
        # l2_xyz, l2_points = self.sa3(l1_xyz, l1_points)
        # l3_xyz, l3_points = self.sa3(l2_xyz, l2_points)

        field_feature = self.sa2_conv1(field_feature)
        field_feature = self.relu(self.fbn21(field_feature))
        field_feature = self.sa2_conv2(field_feature)
        field_feature = self.relu(self.fbn22(field_feature))
        field_feature = self.sa2_conv3(field_feature)
        field_feature = self.relu(self.fbn23(field_feature))

        field_feature = self.sa3_conv1(field_feature)
        field_feature = self.relu(self.fbn31(field_feature))
        field_feature = self.sa3_conv2(field_feature)
        field_feature = self.relu(self.fbn32(field_feature))
        field_feature = self.sa3_conv3(field_feature)
        field_feature = self.relu(self.fbn33(field_feature))

        x = field_feature[:, :, 3:].view(batch_size, 1024)
        x = self.drop1(F.relu(self.bn1(self.fc1(x))))
        x = self.drop2(F.relu(self.bn2(self.fc2(x))))
        x = self.fc3(x)

        return {"pred_label": x, }


def test():
    """The test function just for the network shape checking.
    """

    torch.manual_seed(0)
    dim_b = 4
    dim_n = 1600
    batch = {
        "dist_map": torch.randn(dim_b, dim_n, dim_n),
        "padded_verts": torch.randn(dim_b, dim_n, 3),
        "lrf": torch.randn(dim_b, dim_n, 3, 3),
        "label": torch.randn(dim_b),
        "normal": torch.randn(dim_b, dim_n, 3),
        "xyz": torch.randn(dim_b, 3, dim_n),
        "xyz_sdf": torch.randn(dim_b, dim_n, 4)
    }

    options = EasyDict()
    options.model = EasyDict()

    # options.model.base_dim = 4
    # options.model.base_radius = 0.05
    options.model.out_channel = 2

    gkcnet = Net(options)

    out = gkcnet(batch)

    print(out)


if __name__ == '__main__':
    test()