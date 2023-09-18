import mmap
import pickle

import numpy as np
import torch
import torch.nn as nn
from net import SimpleNet
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


class MyDataset(Dataset):
    def __init__(self, block_size, ):
        with open("../datas/index.pkl", 'rb') as f:
            self.index_list = pickle.load(f)

        self.data_n = len(self.index_list)
        self.block_size = block_size

        symbols = [f"{i}.SH".zfill(9) for i in range(1, 251)]
        times = ["2020.01." + f"{i+1}".zfill(2) for i in range(31)]

        mp_dict = dict()

        for id, symbol in enumerate(symbols):
            for t in times:
                if id >= 10:
                    mp_dict[f"datas/{symbol}-{t}.bin"] = mp_dict[f"datas/{symbols[id % 10]}-{t}.bin"]
                    continue
                f = open(f"../datas/{symbol}-{t}.bin", 'rb')
                mp_f = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                mp_dict[f"datas/{symbol}-{t}.bin"] = [f, mp_f]
        self.mp_dict = mp_dict
        self.symbols = symbols
        self.times = times

    def __len__(self):
        return self.data_n

    def __del__(self):
        for id, symbol in enumerate(self.symbols):
            if id >= 10:
                continue
            for t in self.times:
                f, mp_f = self.mp_dict[f"datas/{symbol}-{t}.bin"]
                mp_f.close()
                f.close()
    
    def __getitem__(self, index):
        x_infos = self.index_list[index]["x"]
        y_infos = self.index_list[index]["y"]
        x_datas = []
        for x_info in x_infos:
            f, mp_f = self.mp_dict[x_info[0]]
            mp_f.seek(x_info[1]*8*1000)
            data = mp_f.read((x_info[2] - x_info[1])*8*1000)
            data = np.frombuffer(data, dtype=np.float64)
            data = data.reshape(-1, 1000)
            x_datas.append(data)
        x_datas = np.concatenate(x_datas, axis=0)
        y_datas = []
        for y_info in y_infos:
            f, mp_f = self.mp_dict[y_info[0]]
            mp_f.seek(y_info[1]*8*1)
            data = mp_f.read((y_info[2] - y_info[1])*8*1)
            data = np.frombuffer(data, dtype=np.float64)
            data = data.reshape(-1, 1)
            y_datas.append(data)
        y_datas = np.concatenate(y_datas, axis=0)
        return x_datas, y_datas


def main():
    torch.set_default_tensor_type(torch.DoubleTensor)

    model = SimpleNet()
    model = model.to("cuda")

    loss_fn = nn.MSELoss()
    loss_fn = loss_fn.to("cuda")
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    dataset = MyDataset(4802)
    dataloader = DataLoader(
        dataset, batch_size=64, shuffle=False, num_workers=3,
        pin_memory=True, pin_memory_device="cuda",
        prefetch_factor=5,
    )

    epoch = 10
    model.train()
    for _ in range(epoch):
        for x, y in tqdm(dataloader, mininterval=1):
            x = x.to("cuda")
            y = y.to("cuda")
            y_pred = model(x)
            loss = loss_fn(y_pred, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()


if __name__ == "__main__":
    main()
