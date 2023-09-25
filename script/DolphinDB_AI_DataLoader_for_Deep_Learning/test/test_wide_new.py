import dolphindb as ddb
import torch
import torch.nn as nn
from net import SimpleNet
from tqdm import tqdm

from dolphindb_tools.dataloader import DDBDataLoader


def main():
    torch.set_default_tensor_type(torch.DoubleTensor)

    model = SimpleNet()
    model = model.to("cuda")
    loss_fn = nn.MSELoss()
    loss_fn = loss_fn.to("cuda")
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)

    symbols = ["`" + f"{i}.SH".zfill(9) for i in range(1, 251)]
    times = ["2020.01." + f"{i+1}".zfill(2) for i in range(31)]

    s = ddb.session()
    s.connect("127.0.0.1", 7940, "admin", "123456")

    dbPath = "dfs://test_ai_dataloader"
    tbName = "wide_factor_table"

    sql = f"""select * from loadTable("{dbPath}", "{tbName}")"""

    dataloader = DDBDataLoader(
        s, sql, targetCol=["f000001"], batchSize=64, shuffle=True,
        windowSize=[200, 1], windowStride=[1, 1],
        repartitionCol="date(DateTime)", repartitionScheme=times,
        groupCol="Symbol", groupScheme=symbols,
        seed=0,
        offset=200, excludeCol=[], device="cuda",
        prefetchBatch=5, prepartitionNum=3
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
