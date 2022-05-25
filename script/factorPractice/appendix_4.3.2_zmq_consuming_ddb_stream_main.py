# -*- coding: utf-8 -*-

'''
python版本: >=3.6

依赖包:
conda install pyzmq
'''

from asyncio import run
from zmq import SUB, SUBSCRIBE, TCP_KEEPALIVE, TCP_KEEPALIVE_CNT, TCP_KEEPALIVE_IDLE, TCP_KEEPALIVE_INTVL
from zmq.asyncio import Context

class async_zmq_streaming_subscriber(object):
	def __init__(self, zmp_subscribing_port:int):
		super(async_zmq_streaming_subscriber, self).__init__()
		self._port=zmp_subscribing_port
		self.zmq_context = Context()
		self.zmq_bingding_socket = self.zmq_context.socket(SUB)

		self.zmq_bingding_socket.setsockopt(TCP_KEEPALIVE, 1)# 保活
		self.zmq_bingding_socket.setsockopt(TCP_KEEPALIVE_CNT, 5)  # 保活包没有响应超过5次，执行重连
		self.zmq_bingding_socket.setsockopt(TCP_KEEPALIVE_IDLE, 60)#空闲超过60秒判定需要发送保活包
		self.zmq_bingding_socket.setsockopt(TCP_KEEPALIVE_INTVL, 3)  #保活包发送间隔3秒
		self.zmq_bingding_socket.setsockopt_string(SUBSCRIBE, "")#指定订阅频道，必须

		zmq_sub_address = f"tcp://*:{zmp_subscribing_port}"
		self.zmq_bingding_socket.bind(zmq_sub_address)
		pass

	async def loop_runner(self):

		print(f"zmq端口{self._port}开始sub监听")

		while True:
			msg=await self.zmq_bingding_socket.recv()
			print(msg)#显示订阅收到的消息

	def run(self):
		run(self.loop_runner())

if __name__ == '__main__':
	current_server_instance=async_zmq_streaming_subscriber(zmp_subscribing_port=55556)
	current_server_instance.run()

