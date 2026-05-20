import torch

torch.manual_seed(42)
normal_logs = torch.randn(1000, 10).to('cuda')
anomaly = torch.tensor([[10.0]*10]).to('cuda')

encoder = torch.nn.Sequential(
    torch.nn.Linear(10, 5),
    torch.nn.ReLU(),
    torch.nn.Linear(5, 2)
).to('cuda')

decoder = torch.nn.Sequential(
    torch.nn.Linear(2, 5),
    torch.nn.ReLU(),
    torch.nn.Linear(5, 10)
).to('cuda')

out = decoder(encoder(anomaly))
loss = torch.nn.MSELoss()(out, anomaly)
print(f'Anomaly score: {loss.item():.4f}')
print(f'Device: {out.device}')
print('Kalpixk motor OK en MI300X')
