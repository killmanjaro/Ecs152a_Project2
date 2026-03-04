import socket
import struct
import random
import sys
import time

#Constants
DNS_PORT = 53
TIMEOUT = 10
MAX_DEPTH = 10 

# Official IANA root server IPv4 addresses
ROOT_SERVERS = [
    "198.41.0.4",    
    "199.9.14.201",   
    "192.33.4.12",    
    "199.7.91.13",    
    "192.203.230.10", 
    "192.5.5.241",    
    "192.112.36.4",   
    "198.97.190.53", 
    "192.36.148.17",  
    "192.58.128.30",  
    "193.0.14.129",   
    "199.7.83.42",    
    "202.12.27.33"    
]

RECORD_TYPES = {
    1: "A",
    2: "NS",
    5: "CNAME",
    28: "AAAA"
}

#DNS Packet Builder 
def build_dns_query(domain):
    transaction_id = random.randint(0, 65535)
    flags = 0x0000  # standard query
    qdcount = 1
    ancount = nscount = arcount = 0

    header = struct.pack(
        "!HHHHHH",
        transaction_id,
        flags,
        qdcount,
        ancount,
        nscount,
        arcount
    )

    qname = b""
    for label in domain.split("."):
        qname += struct.pack("B", len(label)) + label.encode()
    qname += b"\x00"

    qtype = 1   # A
    qclass = 1  # IN

    question = qname + struct.pack("!HH", qtype, qclass)
    return header + question

#DNS Parsing Helper
def parse_name(data, offset):
    labels = []
    jumped = False
    original_offset = offset

    while True:
        length = data[offset]
        if length & 0xC0 == 0xC0:  # pointer
            pointer = struct.unpack("!H", data[offset:offset+2])[0]
            offset = pointer & 0x3FFF
            jumped = True
        elif length == 0:
            offset += 1
            break
        else:
            offset += 1
            labels.append(data[offset:offset+length].decode())
            offset += length

    if jumped:
        return ".".join(labels), original_offset + 2
    return ".".join(labels), offset

def parse_resource_record(data, offset):
    name, offset = parse_name(data, offset)
    rtype, rclass, ttl, rdlength = struct.unpack("!HHIH", data[offset:offset+10])
    offset += 10

    rdata = data[offset:offset+rdlength]
    offset += rdlength

    value = None
    if rtype == 1:  # A
        value = socket.inet_ntoa(rdata)
    elif rtype == 28:  # AAAA
        value = socket.inet_ntop(socket.AF_INET6, rdata)
    elif rtype in (2, 5):  # NS or CNAME
        value, _ = parse_name(data, offset - rdlength)

    return {
        "type": RECORD_TYPES.get(rtype, str(rtype)),
        "value": value
    }, offset

#DNS Query
def dns_query(server_ip, domain):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    packet = build_dns_query(domain)

    start = time.time()
    sock.sendto(packet, (server_ip, DNS_PORT))
    response, _ = sock.recvfrom(512)
    rtt = (time.time() - start) * 1000
    sock.close()

    qdcount, ancount, nscount, arcount = struct.unpack("!HHHH", response[4:12])

    offset = 12
    for _ in range(qdcount):
        _, offset = parse_name(response, offset)
        offset += 4

    answers, authorities, additionals = [], [], []

    for _ in range(ancount):
        rr, offset = parse_resource_record(response, offset)
        answers.append(rr)

    for _ in range(nscount):
        rr, offset = parse_resource_record(response, offset)
        authorities.append(rr)

    for _ in range(arcount):
        rr, offset = parse_resource_record(response, offset)
        additionals.append(rr)

    return answers, authorities, additionals, rtt

# Iterative Resolver
def resolve_domain(domain, depth=0):
    if depth > MAX_DEPTH:
        raise RuntimeError("Maximum DNS resolution depth exceeded")

    servers = ROOT_SERVERS[:]

    while True:
        server = servers[0]

        print("--------------------------------------------")
        print(f"Querying {server} for {domain}")
        print("--------------------------------------------")

        answers, authorities, additionals, rtt = dns_query(server, domain)

        for rr in answers:
            print(f"{rr['type']} : {rr['value']}")
        for rr in authorities:
            print(f"{rr['type']} : {rr['value']}")
        for rr in additionals:
            print(f"{rr['type']} : {rr['value']}")

        print(f"RTT: {rtt:.2f} ms")

        # Final answer found
        for rr in answers:
            if rr["type"] == "A":
                return rr["value"]

        # Prefer glue records
        next_servers = [rr["value"] for rr in additionals if rr["type"] == "A"]

        # Handle glue-less NS referral
        if not next_servers:
            ns_names = [rr["value"] for rr in authorities if rr["type"] == "NS"]
            if not ns_names:
                raise RuntimeError("No NS records to continue resolution")

            # Resolve NS hostname to IP
            ns_ip = resolve_domain(ns_names[0], depth + 1)
            next_servers = [ns_ip]

        servers = next_servers

#HTTP Request 
def make_http_request(ip, domain):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    start = time.time()
    sock.connect((ip, 80))

    request = (
        f"GET / HTTP/1.1\r\n"
        f"Host: {domain}\r\n"
        f"Connection: close\r\n\r\n"
    )

    sock.sendall(request.encode())
    response = sock.recv(1024).decode(errors="ignore")
    rtt = (time.time() - start) * 1000
    sock.close()

    status_line = response.split("\r\n")[0]
    return status_line, rtt

# Main 
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 DNS_client.py <domain>")
        sys.exit(1)

    domain = sys.argv[1]

    final_ip = resolve_domain(domain)

    print("--------------------------------------------")
    print(f"Making HTTP request to {final_ip}")
    print("--------------------------------------------")

    status, rtt = make_http_request(final_ip, domain)
    print(status)
    print(f"RTT: {rtt:.2f} ms")
