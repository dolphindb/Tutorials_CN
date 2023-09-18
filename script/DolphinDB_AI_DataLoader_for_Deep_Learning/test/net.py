import torch
import torch.nn as nn


class SimpleNet(nn.Module):
    def __init__(self) -> None:
        super(SimpleNet, self).__init__()
        self.channels = [200, 100, 50]
        self.features_in = 1000
        self.features_out = 1
        self.conv1d_1 = nn.Conv1d(self.channels[0], self.channels[1], 10, 2, 4)
        self.conv1d_2 = nn.Conv1d(self.channels[1], self.channels[2], 10, 2, 4)
        self.fc1 = nn.Linear(self.channels[2] * self.features_in//4, self.features_in)
        self.fc2 = nn.Linear(self.features_in, self.features_out)
        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor):
        x = self.conv1d_1(x)
        x = self.relu(x)
        x = self.conv1d_2(x)
        x = self.relu(x)
        x = x.flatten(start_dim=1)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        x = x.reshape([-1, 1, self.features_out])
        return x
