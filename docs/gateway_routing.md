# Gateway and Routing Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 기본 게이트웨이, 라우팅 테이블, 외부 네트워크 통신, VLAN 간 라우팅, NAT, 다중 인터페이스, VPN 라우팅 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

게이트웨이 또는 라우팅 문제는 보통 같은 네트워크 내부 통신은 가능하지만 외부 네트워크나 인터넷 접속이 안 될 때 의심할 수 있다. 예를 들어 같은 공유기에 연결된 장비끼리는 ping이 되는데 8.8.8.8 같은 외부 IP로 ping이 안 되거나, 특정 네트워크 대역으로만 접속이 안 되는 경우가 대표적이다.

사용자는 보통 다음처럼 표현한다.

- 내부망은 되는데 인터넷이 안 된다
- 같은 LAN에서는 ping이 되는데 외부로는 안 나간다
- 게이트웨이 ping이 안 된다
- 기본 게이트웨이가 비어 있다
- 라우팅 테이블이 이상하다
- 특정 대역으로만 통신이 안 된다
- VPN 연결 후 인터넷이 안 된다
- VM은 되는데 호스트는 안 된다
- 게이트웨이는 있는데 외부 IP가 안 된다
- traceroute가 중간에서 멈춘다

에이전트는 사용자의 증상을 듣고 먼저 다음을 구분해야 한다.

- IP 주소 자체를 정상적으로 받았는지
- 서브넷 마스크가 올바른지
- 기본 게이트웨이가 설정되어 있는지
- 게이트웨이 IP가 같은 네트워크 대역에 있는지
- 게이트웨이로 ping이 되는지
- 라우팅 테이블에 default route가 있는지
- 특정 목적지 네트워크에 대한 route가 잘못 잡혀 있는지
- 다중 인터페이스 환경에서 잘못된 경로가 우선되는지
- VPN이 기본 라우트를 변경했는지
- VLAN 간 라우팅이 구성되어 있는지
- NAT가 필요한 구간에서 NAT가 동작하는지
- 라우터/L3 스위치/방화벽에서 경로가 끊겼는지

게이트웨이와 라우팅 문제를 정확히 판단하려면 `IP 주소`, `서브넷 마스크`, `기본 게이트웨이`, `라우팅 테이블`, `목적지 IP`, `나가는 인터페이스`, `traceroute 결과`, `NAT 여부`, `VLAN 구조`, `VPN 여부`를 함께 확인해야 한다.

---

## 관련 사용자 표현

사용자는 게이트웨이나 라우팅이라는 용어를 직접 말하지 않을 수도 있다. 다음 표현은 gateway 또는 routing 문제와 관련될 가능성이 있다.

- 인터넷이 안 돼
- 외부망이 안 돼
- 내부망은 되는데 인터넷이 안 돼
- 같은 공유기에 연결된 PC는 ping이 돼
- 같은 LAN은 되는데 밖으로 안 나가져
- 8.8.8.8 ping이 안 돼
- 게이트웨이 ping이 안 돼
- 기본 게이트웨이가 없어
- default gateway가 비어 있어
- ip route에 default가 없어
- route print가 이상해
- 라우팅 테이블이 이상해
- 특정 IP 대역만 안 돼
- 특정 서버만 안 붙어
- traceroute가 중간에서 끊겨
- tracert가 첫 번째 홉에서 멈춰
- VPN 켜면 인터넷이 안 돼
- VPN 연결하면 특정 대역만 안 돼
- VM에서 인터넷이 안 돼
- VirtualBox NAT는 되는데 Bridge가 안 돼
- Host-only에서는 인터넷이 안 돼
- VLAN끼리 통신이 안 돼
- 다른 VLAN으로 ping이 안 돼
- 라우터를 거쳐야 하는데 안 돼
- L3 스위치 설정 문제 같아
- default route가 뭔지 모르겠어
- 게이트웨이랑 라우터 차이가 뭐야
- IP는 받았는데 인터넷 없음이라고 나와
- DNS 문제가 아닌 것 같은데 사이트가 안 돼
- ping google.com도 안 되고 ping 8.8.8.8도 안 돼
- 게이트웨이 주소는 있는데 접속이 안 돼
- 서브넷 마스크가 틀린 것 같아
- NAT 문제인가?
- 공유기 뒤에서는 되는데 외부에서는 안 돼
- 사설 IP에서 공인 IP로 못 나가
- 라우터 설정을 바꿨더니 인터넷이 안 돼

---

## 핵심 개념

네트워크에서 다른 네트워크로 나가기 위해서는 라우팅이 필요하다. 같은 LAN 내부 통신은 보통 스위치와 ARP를 통해 직접 이루어지지만, 다른 네트워크 대역이나 인터넷으로 나가려면 라우터 또는 기본 게이트웨이를 거쳐야 한다.

예를 들어 PC가 다음 IP를 가지고 있다고 가정한다.

```text
PC IP: 192.168.1.10
Subnet Mask: 255.255.255.0
Default Gateway: 192.168.1.1
```

이 PC는 `192.168.1.0/24` 대역의 장비와는 같은 네트워크라고 판단한다.

```text
192.168.1.20 -> 같은 네트워크
192.168.1.30 -> 같은 네트워크
192.168.2.10 -> 다른 네트워크
8.8.8.8 -> 다른 네트워크
```

같은 네트워크로 보낼 때는 목적지 장비의 MAC 주소를 ARP로 찾고 직접 보낸다.  
다른 네트워크로 보낼 때는 목적지 IP를 직접 찾는 것이 아니라 기본 게이트웨이의 MAC 주소를 찾아 게이트웨이로 보낸다.

즉, 인터넷으로 나가는 기본 흐름은 다음과 같다.

```text
PC
  ↓
Default Gateway
  ↓
Router / Firewall / NAT
  ↓
ISP
  ↓
Internet
```

기본 게이트웨이나 라우팅 테이블이 잘못되면 IP 주소를 정상적으로 가지고 있어도 외부 통신이 실패할 수 있다.

---

## 기본 게이트웨이란 무엇인가

기본 게이트웨이는 클라이언트가 자신이 직접 도달할 수 없는 네트워크로 패킷을 보낼 때 사용하는 다음 홉 장비이다.

일반 가정에서는 보통 공유기 LAN IP가 기본 게이트웨이이다.

예시:

```text
PC IP: 192.168.0.25
Default Gateway: 192.168.0.1
```

여기서 `192.168.0.1`은 보통 공유기 또는 라우터이다.

회사나 학교에서는 L3 스위치, 라우터, 방화벽의 SVI 또는 인터페이스 IP가 기본 게이트웨이일 수 있다.

예시:

```text
Client VLAN 10: 10.10.10.0/24
Default Gateway: 10.10.10.1

Client VLAN 20: 10.10.20.0/24
Default Gateway: 10.10.20.1
```

기본 게이트웨이가 없으면 클라이언트는 같은 네트워크 내부로는 통신할 수 있지만 외부 네트워크나 인터넷으로 나갈 수 없다.

---

## 라우팅 테이블이란 무엇인가

라우팅 테이블은 목적지 네트워크별로 패킷을 어디로 보낼지 결정하는 표이다.

운영체제는 패킷을 보낼 때 라우팅 테이블을 확인한다.

Linux:

```bash
ip route
```

Windows:

```cmd
route print
```

라우팅 테이블에는 보통 다음 정보가 있다.

```text
목적지 네트워크
서브넷 마스크 또는 prefix
게이트웨이 또는 next-hop
나가는 인터페이스
metric
```

Linux 예시:

```text
default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

의미:

```text
192.168.1.0/24 대역은 eth0로 직접 보낸다.
그 외 모든 목적지는 192.168.1.1 게이트웨이로 보낸다.
```

Windows 예시:

```text
Network Destination        Netmask          Gateway       Interface  Metric
0.0.0.0                    0.0.0.0          192.168.1.1   192.168.1.10     25
192.168.1.0                255.255.255.0    On-link       192.168.1.10    281
```

여기서 `0.0.0.0/0`은 default route를 의미한다.

---

## Default Route

Default route는 라우팅 테이블에 더 구체적인 경로가 없을 때 사용하는 기본 경로이다.

Linux에서는 다음처럼 보인다.

```text
default via 192.168.1.1 dev eth0
```

Windows에서는 다음처럼 보인다.

```text
0.0.0.0          0.0.0.0          192.168.1.1
```

의미:

```text
어디로 보내야 할지 모르는 목적지는 192.168.1.1로 보낸다.
```

인터넷 접속을 위해서는 일반적으로 default route가 필요하다.

default route가 없으면 다음 증상이 나타날 수 있다.

```text
같은 LAN 내부 ping 성공
게이트웨이 ping 성공
외부 IP ping 실패
인터넷 접속 실패
```

---

## 같은 네트워크와 다른 네트워크 구분

호스트는 IP 주소와 서브넷 마스크를 이용해 목적지가 같은 네트워크인지 판단한다.

예시:

```text
내 IP: 192.168.1.10
서브넷 마스크: 255.255.255.0
네트워크 대역: 192.168.1.0/24
```

목적지 판단:

```text
192.168.1.20 -> 같은 네트워크
192.168.1.254 -> 같은 네트워크
192.168.2.20 -> 다른 네트워크
8.8.8.8 -> 다른 네트워크
```

같은 네트워크이면 게이트웨이를 거치지 않고 직접 ARP를 통해 목적지 MAC 주소를 찾는다.  
다른 네트워크이면 목적지의 MAC을 찾는 것이 아니라 게이트웨이의 MAC 주소를 찾아 게이트웨이로 보낸다.

이 때문에 서브넷 마스크가 틀리면 통신이 이상해질 수 있다.

예시 문제:

```text
정상 설정:
IP: 192.168.1.10
Mask: 255.255.255.0
Gateway: 192.168.1.1

잘못된 설정:
IP: 192.168.1.10
Mask: 255.255.0.0
Gateway: 192.168.1.1
```

서브넷 마스크가 너무 넓으면 원래 게이트웨이로 보내야 할 목적지를 같은 네트워크라고 오해할 수 있다.

---

## Next Hop 개념

Next hop은 목적지까지 가기 위해 다음으로 패킷을 전달할 장비를 의미한다.

예를 들어 PC가 `8.8.8.8`로 패킷을 보낼 때, PC 입장에서 next hop은 실제 8.8.8.8이 아니다. 보통 기본 게이트웨이이다.

```text
PC -> Gateway -> ISP Router -> Internet -> 8.8.8.8
```

각 라우터는 전체 경로를 모두 알 필요 없이 다음 홉을 기준으로 패킷을 전달한다.

라우팅 문제를 진단할 때는 "목적지 IP로 바로 가는가?"가 아니라 "현재 장비의 다음 홉이 올바른가?"를 확인해야 한다.

---

## NAT와 라우팅의 관계

사설 IP 대역은 인터넷에서 직접 라우팅되지 않는다.

대표 사설 IP 대역:

```text
10.0.0.0/8
172.16.0.0/12
192.168.0.0/16
```

가정이나 회사 내부 장비가 인터넷에 접속하려면 보통 NAT가 필요하다.

예시:

```text
내부 PC: 192.168.0.10
공유기 공인 IP: 203.0.113.10
목적지: 8.8.8.8
```

공유기는 내부 사설 IP를 자신의 공인 IP로 변환하여 인터넷으로 내보낸다.

```text
192.168.0.10 -> NAT -> 203.0.113.10
```

따라서 내부 PC에서 게이트웨이까지는 통신되는데 외부 인터넷이 안 된다면 다음도 확인해야 한다.

```text
게이트웨이의 WAN 연결
NAT 설정
상위 라우터 경로
ISP 연결
방화벽 정책
```

라우팅 테이블만 정상이어도 NAT가 동작하지 않으면 사설 IP 장비는 인터넷 응답을 제대로 받을 수 없다.

---

## ICMP와 ping의 한계

ping은 ICMP Echo Request/Reply를 이용한다.

ping은 도달성 확인에 유용하지만, 모든 네트워크 장비가 ICMP에 응답하는 것은 아니다.

주의할 점:

```text
ping 실패 = 무조건 통신 불가 아님
ping 성공 = 모든 서비스 접속 가능 아님
```

일부 방화벽이나 서버는 ICMP를 차단하지만 TCP 80/443은 허용할 수 있다. 반대로 ping은 되지만 TCP 포트가 차단될 수도 있다.

따라서 게이트웨이/라우팅 문제를 진단할 때는 ping, traceroute, route table, DNS, 포트 테스트를 함께 봐야 한다.

---

## traceroute / tracert 개념

traceroute는 목적지까지 가는 경로의 홉을 확인하는 도구이다.

Linux:

```bash
traceroute 8.8.8.8
```

Windows:

```cmd
tracert 8.8.8.8
```

출력 예시:

```text
1  192.168.1.1
2  10.10.0.1
3  203.0.113.1
4  ...
```

의미:

```text
1번 홉: 내 기본 게이트웨이
2번 홉: 상위 라우터 또는 ISP 장비
3번 홉 이후: 인터넷 경로
```

판단 기준:

```text
1번 홉부터 실패:
내 PC와 게이트웨이 사이 문제 가능성.

1번 홉은 성공, 2번 홉부터 실패:
게이트웨이 상위 경로, NAT, WAN, ISP 문제 가능성.

특정 중간 홉에서 멈춤:
해당 구간 이후 라우팅 또는 방화벽 문제 가능성.

별표(*)가 보임:
해당 장비가 TTL exceeded 응답을 차단할 수 있음. 반드시 장애라고 단정하면 안 됨.
```

---

## Gateway/Routing 문제의 대표 증상

### 1. 같은 LAN 내부 장비로는 ping이 되지만 외부 IP로 ping이 안 됨

대표적인 게이트웨이 또는 라우팅 문제 증상이다.

예시:

```text
ping 192.168.1.20 -> 성공
ping 192.168.1.1 -> 성공
ping 8.8.8.8 -> 실패
```

가능한 원인:

- default route 없음
- 기본 게이트웨이 설정 오류
- 게이트웨이의 WAN 연결 문제
- 게이트웨이 NAT 문제
- 상위 라우터 문제
- 방화벽 정책
- ISP 문제
- VPN 라우팅 문제

판단:

```text
LAN 내부 통신은 되므로 NIC, 케이블, 스위치, IP 주소는 대체로 정상일 가능성이 있다.
외부 IP가 안 되므로 default gateway, routing, NAT, upstream 연결을 확인해야 한다.
```

---

### 2. 기본 게이트웨이로 ping이 실패함

예시:

```bash
ping 192.168.1.1
```

실패 원인:

- 게이트웨이 IP가 잘못됨
- 클라이언트 IP/서브넷 마스크가 잘못됨
- 게이트웨이 장비 장애
- VLAN이 다름
- 스위치 포트 VLAN 설정 오류
- ARP 실패
- 케이블/Wi-Fi 연결 문제
- 게이트웨이가 ICMP를 차단
- 방화벽 정책
- IP 충돌
- 클라이언트가 잘못된 네트워크에 연결됨

주의:

게이트웨이가 ICMP를 차단할 수도 있으므로 ping 실패만으로 게이트웨이가 죽었다고 단정하면 안 된다. 하지만 일반적인 LAN 환경에서는 게이트웨이 ping 실패는 매우 중요한 이상 신호이다.

추가 확인:

```bash
ip addr
ip route
arp -a
ip neigh
```

---

### 3. 기본 게이트웨이가 설정되어 있지 않음

Linux:

```bash
ip route
```

문제 예시:

```text
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

default route가 없다.

정상 예시:

```text
default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

Windows:

```cmd
route print
```

문제 예시:

```text
0.0.0.0/0 경로가 없음
```

가능한 원인:

- DHCP에서 gateway option을 받지 못함
- 수동 IP 설정 시 gateway 누락
- NetworkManager 설정 오류
- netplan 설정 오류
- VM 네트워크 설정 오류
- VPN이 default route를 제거
- 관리자가 의도적으로 default route를 제거

증상:

```text
같은 네트워크 내부 통신 가능
외부 네트워크 통신 불가
인터넷 접속 불가
```

---

### 4. 기본 게이트웨이 IP가 잘못 설정됨

예시:

```text
내 IP: 192.168.1.10/24
Gateway: 192.168.2.1
```

게이트웨이는 일반적으로 클라이언트가 직접 도달 가능한 같은 네트워크 대역에 있어야 한다.  
위 예시에서 `192.168.2.1`은 `192.168.1.0/24` 대역 밖이므로 일반적인 환경에서는 잘못된 설정이다.

가능한 증상:

```text
default route는 있어 보이지만 통신 실패
gateway ping 실패
외부 네트워크 접속 실패
```

확인:

```bash
ip addr
ip route
```

Windows:

```cmd
ipconfig /all
route print
```

---

### 5. 특정 네트워크 대역으로만 통신이 안 됨

예시:

```text
인터넷은 됨
10.10.20.0/24 대역만 안 됨
사내 서버 대역만 안 됨
VPN 대역만 안 됨
```

가능한 원인:

- 특정 목적지 대역 route 누락
- 잘못된 static route
- VPN route 누락
- 방화벽 정책
- ACL 차단
- VLAN 간 라우팅 누락
- return route 누락
- overlapping subnet
- NAT 예외 설정 문제

진단:

```bash
ip route get <destination_ip>
traceroute <destination_ip>
ping <destination_ip>
```

Windows:

```cmd
route print
tracert <destination_ip>
```

판단:

```text
default route로 나가면 안 되는 사내 대역이 인터넷 방향으로 나감:
static route 또는 VPN route 누락 가능성.

목적지까지는 가지만 응답이 안 옴:
상대방 return route, 방화벽, ACL 문제 가능성.

특정 대역이 내 로컬 서브넷과 겹침:
overlapping subnet 문제 가능성.
```

---

### 6. VLAN 간 통신이 안 됨

VLAN은 L2 브로드캐스트 도메인을 분리한다. 서로 다른 VLAN끼리 통신하려면 라우터나 L3 스위치에서 inter-VLAN routing이 필요하다.

예시:

```text
VLAN 10: 192.168.10.0/24
VLAN 20: 192.168.20.0/24
```

VLAN 10의 PC가 VLAN 20의 서버와 통신하려면 L3 장비가 두 VLAN의 게이트웨이 역할을 해야 한다.

가능한 원인:

- 각 VLAN의 SVI가 없음
- SVI가 down 상태
- 클라이언트 gateway가 잘못됨
- trunk 포트에 VLAN이 허용되지 않음
- access VLAN 설정 오류
- 라우팅이 비활성화됨
- ACL이 VLAN 간 통신 차단
- 방화벽 정책 차단

판단:

```text
같은 VLAN 내부 통신은 됨
다른 VLAN으로 ping 실패
gateway ping 실패 또는 특정 VLAN gateway만 실패
```

---

### 7. VPN 연결 후 인터넷 또는 특정 대역이 안 됨

VPN은 라우팅 테이블을 변경할 수 있다.

가능한 방식:

```text
Full tunnel:
모든 트래픽이 VPN으로 감.

Split tunnel:
특정 사내 대역만 VPN으로 감.
```

문제 유형:

```text
VPN 연결 후 인터넷이 안 됨:
VPN이 default route를 가져갔지만 VPN 측에서 인터넷 NAT/라우팅이 안 될 수 있음.

VPN 연결 후 사내망이 안 됨:
VPN route push 실패, split route 누락, DNS 문제 가능성.

VPN 연결 후 로컬 LAN 접속이 안 됨:
VPN 정책이 로컬 LAN 접근을 차단할 수 있음.

VPN 대역과 집/학교 LAN 대역이 겹침:
overlapping subnet 문제 가능성.
```

확인:

Linux:

```bash
ip route
ip route get <destination_ip>
```

Windows:

```cmd
route print
tracert <destination_ip>
```

VPN 연결 전후 라우팅 테이블을 비교하는 것이 중요하다.

---

### 8. 다중 인터페이스 환경에서 잘못된 경로로 나감

노트북, 서버, VM 호스트는 여러 인터페이스를 가질 수 있다.

예시:

```text
Wi-Fi
Ethernet
VPN
VirtualBox Host-only
VMware Network
WSL virtual adapter
Docker bridge
Tailscale/ZeroTier
```

여러 인터페이스가 동시에 default route를 가질 수 있고, metric에 따라 우선순위가 결정된다.

문제 예시:

```text
Wi-Fi로 인터넷을 나가야 하는데 VPN이 default route를 가져감
VirtualBox Host-only가 특정 대역 route를 가져감
Docker bridge 대역과 실제 사내망 대역이 겹침
Ethernet과 Wi-Fi가 같은 대역을 사용하여 혼란 발생
```

확인:

Linux:

```bash
ip route
ip route get 8.8.8.8
```

Windows:

```cmd
route print
```

판단:

```text
원하는 인터페이스가 아닌 다른 인터페이스로 나가면 metric 또는 route 우선순위 문제 가능성.
```

---

### 9. VM 네트워크에서 인터넷이 안 됨

가상머신 네트워크 모드에 따라 게이트웨이와 라우팅 구조가 달라진다.

대표 모드:

```text
NAT
Bridge
Host-only
Internal Network
NAT Network
```

각 모드의 특징:

```text
NAT:
VM이 호스트를 통해 외부로 나감. 보통 가상 NAT 게이트웨이가 존재함.

Bridge:
VM이 실제 LAN에 직접 연결된 것처럼 동작. 실제 공유기나 네트워크 게이트웨이를 사용함.

Host-only:
호스트와 VM 사이의 내부 네트워크. 기본적으로 인터넷이 안 될 수 있음.

Internal Network:
VM끼리만 통신. 별도 라우터나 DHCP 서버가 없으면 외부 통신 불가.
```

VM에서 인터넷이 안 되는 경우 확인:

```bash
ip addr
ip route
ping <gateway_ip>
ping 8.8.8.8
```

가능한 원인:

- default route 없음
- VM NAT 게이트웨이 장애
- Bridge 대상 어댑터 오류
- Host-only 모드인데 인터넷을 기대함
- VM 내부 방화벽
- 호스트 방화벽
- DHCP 실패
- DNS 문제

---

## Possible Causes

게이트웨이/라우팅 문제의 원인은 크게 클라이언트 설정 문제, 게이트웨이 장비 문제, 라우팅 테이블 문제, VLAN/L3 설정 문제, NAT 문제, VPN 문제, 다중 인터페이스 문제로 나눌 수 있다.

---

### 1. 기본 게이트웨이가 설정되어 있지 않음

기본 게이트웨이가 없으면 외부 네트워크로 나갈 수 없다.

Linux 확인:

```bash
ip route
```

정상:

```text
default via 192.168.1.1 dev eth0
```

비정상:

```text
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

Windows 확인:

```cmd
ipconfig /all
route print
```

해결 방향:

- DHCP 재요청
- 수동 IP 설정에서 gateway 추가
- NetworkManager 설정 수정
- netplan 설정 수정
- VM 네트워크 모드 확인
- DHCP 서버의 Router Option 확인

NetworkManager 예시:

```bash
sudo nmcli con mod "<connection-name>" ipv4.gateway 192.168.1.1
sudo nmcli con up "<connection-name>"
```

DHCP 사용 시:

```bash
sudo nmcli con mod "<connection-name>" ipv4.method auto
sudo nmcli con up "<connection-name>"
```

---

### 2. 게이트웨이 IP가 잘못 설정됨

게이트웨이는 보통 클라이언트와 같은 L2 네트워크에서 직접 도달 가능해야 한다.

잘못된 예:

```text
Client IP: 192.168.1.10/24
Gateway: 192.168.2.1
```

올바른 예:

```text
Client IP: 192.168.1.10/24
Gateway: 192.168.1.1
```

확인:

```bash
ip addr
ip route
ping <gateway_ip>
```

Windows:

```cmd
ipconfig /all
ping <gateway_ip>
```

가능한 원인:

- 수동 IP 설정 오류
- DHCP 서버의 gateway option 오류
- 잘못된 VLAN에 연결됨
- 잘못된 SSID에 연결됨
- Rogue DHCP 서버가 잘못된 gateway 배포

---

### 3. 서브넷 마스크 오류

서브넷 마스크가 잘못되면 호스트가 목적지를 같은 네트워크로 오해하거나, 반대로 같은 네트워크를 다른 네트워크로 오해할 수 있다.

예시:

```text
정상:
IP: 192.168.1.10
Mask: 255.255.255.0

문제:
IP: 192.168.1.10
Mask: 255.255.0.0
```

문제 가능성:

```text
ARP를 보내면 안 되는 목적지에 ARP를 보냄
게이트웨이로 보내야 할 패킷을 직접 보내려 함
특정 대역 통신만 실패
같은 LAN 일부만 통신
```

확인:

```bash
ip addr
ip route
```

Windows:

```cmd
ipconfig /all
```

---

### 4. 라우팅 테이블에 잘못된 경로가 있음

잘못된 static route나 VPN route가 존재하면 패킷이 엉뚱한 인터페이스로 나갈 수 있다.

확인:

Linux:

```bash
ip route
ip route get <destination_ip>
```

Windows:

```cmd
route print
```

예시:

```bash
ip route get 8.8.8.8
```

출력 예:

```text
8.8.8.8 via 192.168.1.1 dev wlan0 src 192.168.1.10
```

확인할 것:

```text
목적지가 어느 게이트웨이로 나가는가?
어느 인터페이스로 나가는가?
source IP가 무엇인가?
metric이 어떻게 되는가?
```

잘못된 static route 삭제 예시:

Linux:

```bash
sudo ip route del <network>/<prefix>
```

Windows:

```cmd
route delete <network>
```

---

### 5. 라우터 또는 L3 스위치 설정 문제

클라이언트 설정이 정상이어도 라우터나 L3 스위치가 제대로 라우팅하지 못하면 통신이 실패한다.

가능한 원인:

- 라우터 인터페이스 down
- L3 SVI down
- ip routing 비활성화
- static route 누락
- default route 누락
- dynamic routing 문제
- ACL 차단
- VRF 문제
- 라우터 방화벽 정책
- NAT 미설정
- VLAN trunk 문제

증상:

```text
클라이언트는 gateway까지 ping 가능
gateway 이후로 traceroute가 멈춤
특정 대역만 통신 실패
다른 VLAN으로 통신 실패
```

진단 방향:

```text
라우터의 인터페이스 상태 확인
라우터의 라우팅 테이블 확인
목적지 대역으로 가는 route 확인
return path 확인
ACL 확인
NAT 확인
```

---

### 6. VLAN 간 라우팅 미설정

서로 다른 VLAN은 기본적으로 L2에서 분리되어 있으므로 통신할 수 없다. VLAN 간 통신을 위해서는 L3 장비가 필요하다.

필요한 요소:

```text
각 VLAN의 게이트웨이 IP
L3 스위치 SVI 또는 라우터 서브인터페이스
trunk 설정
라우팅 활성화
ACL 허용
```

문제 예시:

```text
VLAN 10 내부 통신 가능
VLAN 20 내부 통신 가능
VLAN 10 -> VLAN 20 통신 불가
```

가능한 원인:

- VLAN 10 SVI는 있는데 VLAN 20 SVI 없음
- trunk에 VLAN 20이 허용되지 않음
- access port VLAN 오설정
- inter-VLAN ACL이 차단
- DHCP는 받았지만 gateway가 잘못됨
- L3 스위치에서 routing 비활성화

---

### 7. NAT 문제

내부 사설 IP에서 인터넷으로 나가려면 NAT가 필요한 경우가 많다.

증상:

```text
내부 PC -> 게이트웨이 ping 성공
내부 PC -> 외부 IP ping 실패
게이트웨이 자체는 외부 인터넷 가능
```

가능한 원인:

- NAT rule 없음
- NAT 대상 인터페이스 오류
- 방화벽 NAT 정책 오류
- outbound masquerade 비활성화
- 사설 IP가 외부로 그대로 나감
- return traffic이 돌아오지 못함

OpenWrt에서는 firewall zone과 masquerading 설정을 확인해야 한다.

확인:

```sh
uci show firewall
ip route
```

Linux 라우터에서는 iptables/nftables NAT 확인:

```bash
sudo iptables -t nat -L -n -v
sudo nft list ruleset
```

---

### 8. Return Route 누락

네트워크 통신은 왕복이 되어야 한다.

클라이언트에서 목적지까지 패킷이 도착해도, 목적지 또는 중간 라우터가 응답을 되돌려 보낼 경로를 모르면 통신은 실패한다.

예시:

```text
A 네트워크: 192.168.10.0/24
B 네트워크: 192.168.20.0/24
```

A에서 B로 가는 route는 있지만, B에서 A로 돌아오는 route가 없으면 통신이 실패한다.

증상:

```text
traceroute는 어느 정도 진행됨
상대 서버에 요청은 도착하는 것 같음
응답이 돌아오지 않음
방화벽 로그에는 inbound만 보임
```

진단:

```text
양쪽 라우팅 테이블 확인
상대방 default gateway 확인
방화벽 state 확인
tcpdump로 request/response 확인
```

---

### 9. Overlapping Subnet 문제

서로 다른 네트워크가 같은 IP 대역을 사용하면 라우팅 문제가 발생한다.

예시:

```text
집 LAN: 192.168.0.0/24
회사 VPN 내부망: 192.168.0.0/24
```

이 경우 PC는 `192.168.0.x` 목적지를 집 LAN이라고 판단할 수 있고, VPN으로 보내지 않을 수 있다.

증상:

```text
VPN 연결은 됨
회사 내부 특정 서버 접속 실패
다른 회사 대역은 됨
집 공유기 대역과 회사 대역이 겹침
```

해결 방향:

```text
집 LAN 대역 변경
VPN 쪽 route 조정
더 구체적인 route 추가
NAT 기반 VPN 설정
관리자에게 대역 충돌 보고
```

---

### 10. VPN 라우팅 문제

VPN 클라이언트는 라우팅 테이블에 새로운 route를 추가한다.

문제 가능성:

- VPN route push 실패
- split tunnel route 누락
- default route가 VPN으로 변경됨
- VPN metric이 너무 높거나 낮음
- VPN DNS와 routing이 맞지 않음
- 로컬 LAN 접근 차단
- overlapping subnet
- VPN 서버 측 return route 누락

확인:

```bash
ip route
ip route get <internal_ip>
```

Windows:

```cmd
route print
```

VPN 연결 전후 라우팅 테이블을 비교해야 한다.

---

### 11. 다중 Default Gateway 문제

여러 인터페이스가 동시에 default gateway를 가질 수 있다.

예시:

```text
Wi-Fi default gateway: 192.168.0.1
Ethernet default gateway: 192.168.56.1
VPN default gateway: 10.8.0.1
```

운영체제는 metric이 낮은 경로를 우선할 수 있다.

문제:

```text
인터넷은 Wi-Fi로 나가야 하는데 VM Host-only 쪽으로 나감
VPN을 켰더니 모든 트래픽이 VPN으로 감
유선과 무선이 동시에 연결되어 경로가 꼬임
```

확인:

Linux:

```bash
ip route
ip route get 8.8.8.8
```

Windows:

```cmd
route print
```

해결 방향:

```text
사용하지 않는 인터페이스 비활성화
metric 조정
불필요한 default route 삭제
VPN split tunneling 설정
정확한 static route 추가
```

---

## Recommended Commands

게이트웨이와 라우팅 문제는 운영체제별로 확인 명령어가 다르다.

---

## Windows 클라이언트 진단 명령어

### 전체 IP 설정 확인

```cmd
ipconfig /all
```

확인할 항목:

```text
IPv4 Address
Subnet Mask
Default Gateway
DNS Servers
DHCP Enabled
DHCP Server
```

판단 기준:

```text
Default Gateway가 없음:
외부 네트워크 통신 불가 가능성.

IPv4가 169.254.x.x:
DHCP 문제 가능성이 높음.

Gateway가 IP 대역과 맞지 않음:
수동 설정 오류 또는 DHCP option 오류 가능성.

DNS만 이상함:
라우팅이 아니라 DNS 문제일 수 있음.
```

### 라우팅 테이블 확인

```cmd
route print
```

확인할 항목:

```text
0.0.0.0/0 default route 존재 여부
gateway 주소
interface 주소
metric
특정 목적지 대역 route
VPN route
```

### 기본 게이트웨이 ping

```cmd
ping <gateway_ip>
```

### 외부 IP ping

```cmd
ping 8.8.8.8
```

### 도메인 ping

```cmd
ping google.com
```

판단:

```text
8.8.8.8 실패 + google.com 실패:
DNS 이전의 라우팅/게이트웨이 문제 가능성.

8.8.8.8 성공 + google.com 실패:
DNS 문제 가능성.
```

### 경로 추적

```cmd
tracert 8.8.8.8
```

특정 목적지:

```cmd
tracert <destination_ip>
```

### 특정 route 추가

```cmd
route add <network> mask <netmask> <gateway>
```

예시:

```cmd
route add 10.10.20.0 mask 255.255.255.0 192.168.1.1
```

### 특정 route 삭제

```cmd
route delete <network>
```

---

## Linux 클라이언트 진단 명령어

### IP 주소 확인

```bash
ip addr
```

또는:

```bash
ip a
```

확인할 항목:

```text
인터페이스 UP 여부
IPv4 주소
prefix 길이
예상한 대역인지
```

### 라우팅 테이블 확인

```bash
ip route
```

정상 예시:

```text
default via 192.168.1.1 dev eth0
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.10
```

문제 예시:

```text
default route 없음
gateway가 잘못됨
원하지 않는 인터페이스가 default route를 가짐
```

### 특정 목적지로 나가는 경로 확인

```bash
ip route get <destination_ip>
```

예시:

```bash
ip route get 8.8.8.8
ip route get 10.10.20.10
```

출력 예:

```text
8.8.8.8 via 192.168.1.1 dev eth0 src 192.168.1.10
```

확인할 것:

```text
next-hop이 맞는가?
나가는 인터페이스가 맞는가?
source IP가 맞는가?
```

### 게이트웨이 ping

```bash
ping <gateway_ip>
```

### 외부 IP ping

```bash
ping 8.8.8.8
```

### traceroute

```bash
traceroute 8.8.8.8
```

설치가 안 되어 있으면 패키지 설치가 필요할 수 있다.

대체 명령어:

```bash
tracepath 8.8.8.8
```

### ARP/Neighbor 확인

```bash
ip neigh
```

또는:

```bash
arp -a
```

게이트웨이에 대한 MAC 주소가 정상적으로 잡히는지 확인한다.

문제 예시:

```text
192.168.1.1 dev eth0 FAILED
192.168.1.1 dev eth0 INCOMPLETE
```

이는 게이트웨이 ARP가 실패하고 있음을 의미할 수 있다.

### 임시 default route 추가

```bash
sudo ip route add default via <gateway_ip> dev <interface>
```

예시:

```bash
sudo ip route add default via 192.168.1.1 dev eth0
```

### default route 변경

```bash
sudo ip route replace default via <gateway_ip> dev <interface>
```

### 특정 route 추가

```bash
sudo ip route add <network>/<prefix> via <gateway_ip>
```

예시:

```bash
sudo ip route add 10.10.20.0/24 via 192.168.1.1
```

### route 삭제

```bash
sudo ip route del <network>/<prefix>
```

예시:

```bash
sudo ip route del 10.10.20.0/24
```

주의:

`ip route add`로 추가한 route는 재부팅 후 사라질 수 있다. 영구 설정은 NetworkManager, netplan, systemd-networkd 등 환경에 맞는 방식으로 해야 한다.

---

## NetworkManager 환경 진단

NetworkManager를 사용하는 Linux에서는 다음 명령어가 유용하다.

### 장치 상태 확인

```bash
nmcli dev status
```

### 장치 상세 확인

```bash
nmcli dev show
```

확인할 항목:

```text
IP4.ADDRESS
IP4.GATEWAY
IP4.ROUTE
IP4.DNS
IP4.DHCP_SERVER
```

### 연결 프로파일 확인

```bash
nmcli con show
```

특정 연결 확인:

```bash
nmcli con show "<connection-name>"
```

### DHCP로 자동 설정

```bash
sudo nmcli con mod "<connection-name>" ipv4.method auto
sudo nmcli con up "<connection-name>"
```

### 수동 gateway 설정

```bash
sudo nmcli con mod "<connection-name>" ipv4.gateway 192.168.1.1
sudo nmcli con up "<connection-name>"
```

### 수동 IP, gateway, DNS 설정 예시

```bash
sudo nmcli con mod "<connection-name>" ipv4.method manual
sudo nmcli con mod "<connection-name>" ipv4.addresses 192.168.1.10/24
sudo nmcli con mod "<connection-name>" ipv4.gateway 192.168.1.1
sudo nmcli con mod "<connection-name>" ipv4.dns "8.8.8.8 1.1.1.1"
sudo nmcli con up "<connection-name>"
```

---

## OpenWrt 라우팅 진단 명령어

OpenWrt 라우터에서는 다음을 확인한다.

### 인터페이스 IP 확인

```sh
ip addr
```

### 라우팅 테이블 확인

```sh
ip route
```

### UCI 네트워크 설정 확인

```sh
uci show network
```

### 방화벽/NAT 설정 확인

```sh
uci show firewall
```

### WAN 상태 확인

```sh
ifstatus wan
```

### LAN 상태 확인

```sh
ifstatus lan
```

### 게이트웨이 ping

```sh
ping 8.8.8.8
```

### DNS 확인

```sh
nslookup google.com
```

### 로그 확인

```sh
logread
```

OpenWrt에서 인터넷이 안 될 때 확인할 것:

```text
WAN 인터페이스가 IP를 받았는가?
WAN default route가 있는가?
LAN 클라이언트의 gateway가 OpenWrt LAN IP인가?
firewall zone에서 LAN -> WAN forwarding이 허용되는가?
WAN zone masquerading이 켜져 있는가?
DNS 설정이 정상인가?
```

---

## Packet Capture로 라우팅 확인

라우팅 문제는 tcpdump로 패킷이 어느 인터페이스로 나가는지 확인하면 도움이 된다.

### 특정 목적지 패킷 확인

```bash
sudo tcpdump -i <interface> -n host <destination_ip>
```

예시:

```bash
sudo tcpdump -i eth0 -n host 8.8.8.8
```

### 게이트웨이 ARP 확인

```bash
sudo tcpdump -i <interface> -n arp
```

판단:

```text
게이트웨이 ARP 요청만 반복되고 응답 없음:
게이트웨이 IP 오류, VLAN 문제, L2 연결 문제 가능성.

패킷이 잘못된 인터페이스로 나감:
라우팅 테이블 또는 metric 문제 가능성.

패킷은 나가는데 응답이 없음:
게이트웨이 이후 경로, NAT, 방화벽, return route 문제 가능성.

요청과 응답이 모두 보임:
네트워크 경로는 정상일 수 있으며 상위 애플리케이션 문제 가능성.
```

---

## 단계별 진단 절차

게이트웨이/라우팅 문제는 다음 순서로 진단하는 것이 좋다.

---

### 1단계: 현재 IP 설정 확인

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
ip addr
```

확인할 것:

```text
IP 주소가 있는가?
169.254.x.x가 아닌가?
서브넷 마스크가 맞는가?
기본 게이트웨이가 있는가?
DNS 서버가 있는가?
```

판단:

```text
IP가 169.254.x.x:
DHCP 문제 가능성이 높다.

IP는 정상인데 gateway 없음:
라우팅 문제 가능성이 높다.

gateway는 있는데 DNS 없음:
DNS 문제 가능성이 있다.
```

---

### 2단계: 라우팅 테이블 확인

Windows:

```cmd
route print
```

Linux:

```bash
ip route
```

확인할 것:

```text
default route가 있는가?
default gateway가 올바른가?
나가는 인터페이스가 맞는가?
특정 목적지 route가 잘못되어 있지 않은가?
metric 우선순위가 이상하지 않은가?
VPN route가 추가되어 있는가?
```

---

### 3단계: 게이트웨이 ping 확인

```bash
ping <gateway_ip>
```

판단:

```text
gateway ping 성공:
클라이언트와 게이트웨이 사이의 기본 L2/L3 연결은 가능할 확률이 높다.

gateway ping 실패:
IP 대역, 서브넷 마스크, VLAN, ARP, 게이트웨이 장애, 방화벽 문제 가능성.
```

추가 확인:

```bash
ip neigh
arp -a
```

---

### 4단계: 외부 IP 통신 확인

```bash
ping 8.8.8.8
```

판단:

```text
gateway ping 성공 + 8.8.8.8 실패:
게이트웨이 이후 라우팅, NAT, WAN, 방화벽, ISP 문제 가능성.

8.8.8.8 성공:
외부 IP 통신은 가능. 도메인 접속이 안 되면 DNS 문제 가능성.
```

---

### 5단계: DNS와 구분

```bash
ping google.com
nslookup google.com
```

판단:

```text
8.8.8.8 성공 + google.com 실패:
DNS 문제 가능성.

8.8.8.8 실패 + google.com 실패:
DNS 이전의 게이트웨이/라우팅 문제 가능성.
```

---

### 6단계: traceroute로 경로 확인

Linux:

```bash
traceroute 8.8.8.8
```

Windows:

```cmd
tracert 8.8.8.8
```

판단:

```text
첫 번째 홉부터 실패:
내 PC와 게이트웨이 사이 문제 가능성.

첫 번째 홉은 게이트웨이로 보이고 이후 실패:
게이트웨이 이후 라우팅, NAT, WAN, ISP 문제 가능성.

특정 중간 홉 이후 실패:
해당 구간 이후 경로 문제 또는 ICMP 차단 가능성.
```

---

### 7단계: 특정 목적지 경로 확인

Linux:

```bash
ip route get <destination_ip>
```

Windows:

```cmd
route print
```

확인할 것:

```text
목적지가 어느 gateway로 나가는가?
어느 interface로 나가는가?
VPN으로 나가야 하는데 일반 gateway로 나가고 있지는 않은가?
인터넷으로 나가야 하는데 VPN으로 나가고 있지는 않은가?
```

---

### 8단계: 다중 인터페이스와 VPN 확인

확인할 것:

```text
Wi-Fi와 Ethernet이 동시에 연결되어 있는가?
VPN이 default route를 가져갔는가?
VirtualBox/VMware/WSL/Docker route가 우선되는가?
metric이 이상하지 않은가?
overlapping subnet이 있는가?
```

명령어:

```bash
ip route
ip route get 8.8.8.8
```

Windows:

```cmd
route print
```

---

### 9단계: 라우터/NAT/상위 장비 확인

클라이언트 설정이 정상이라면 게이트웨이 장비를 확인한다.

확인할 것:

```text
게이트웨이 장비가 인터넷에 연결되어 있는가?
게이트웨이 장비 자체에서 8.8.8.8 ping이 되는가?
WAN IP를 받았는가?
NAT가 활성화되어 있는가?
방화벽에서 LAN -> WAN이 허용되어 있는가?
상위 라우터로 default route가 있는가?
```

OpenWrt:

```sh
ifstatus wan
ip route
uci show firewall
ping 8.8.8.8
```

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
같은 LAN ping 성공 + 외부 IP ping 실패:
기본 게이트웨이, default route, NAT, WAN, 상위 라우팅 문제 가능성이 높다.

기본 게이트웨이 없음:
외부 네트워크로 나갈 경로가 없으므로 gateway 설정 또는 DHCP Router Option을 확인해야 한다.

기본 게이트웨이 ping 실패:
게이트웨이 IP 오류, VLAN 문제, 서브넷 마스크 오류, ARP 실패, L2 연결 문제 가능성이 있다.

기본 게이트웨이 ping 성공 + 8.8.8.8 실패:
게이트웨이 이후 경로, NAT, 방화벽, ISP 문제 가능성이 있다.

8.8.8.8 ping 성공 + google.com 실패:
gateway/routing보다는 DNS 문제 가능성이 높다.

ip route에 default via가 없음:
default route 누락으로 인터넷 접속이 어려울 가능성이 높다.

route print에 0.0.0.0/0 경로가 없음:
Windows에서 default route 누락 가능성이 높다.

특정 대역만 통신 실패:
static route 누락, VPN route 누락, ACL, return route, overlapping subnet 문제 가능성이 있다.

VPN 연결 후 인터넷 실패:
VPN이 default route를 가져갔거나 VPN 서버 측 NAT/라우팅 문제 가능성이 있다.

VPN 연결 후 사내망 실패:
VPN split route, DNS, 내부 route push 문제 가능성이 있다.

다중 인터페이스 환경에서 이상한 인터페이스로 나감:
metric 또는 route 우선순위 문제 가능성이 있다.

traceroute가 첫 번째 홉에서 실패:
클라이언트와 게이트웨이 사이 문제 가능성이 높다.

traceroute가 게이트웨이 이후에서 실패:
상위 라우터, NAT, WAN, ISP, 방화벽 문제 가능성이 높다.

게이트웨이 ARP가 INCOMPLETE 또는 FAILED:
게이트웨이와 L2 연결이 되지 않거나 IP/VLAN이 잘못되었을 가능성이 있다.

라우터는 외부 인터넷이 되는데 클라이언트만 안 됨:
LAN 클라이언트 gateway, NAT, firewall forwarding 문제 가능성이 있다.

클라이언트에서 패킷은 나가지만 응답이 안 옴:
return route, NAT, 방화벽 문제 가능성이 있다.
```

---

## 문제 유형별 해결 방법

### 기본 게이트웨이가 없을 때

1. DHCP를 사용하는지 확인
2. DHCP에서 gateway option을 받았는지 확인
3. 수동 IP 설정이면 gateway를 추가
4. NetworkManager 또는 netplan 설정 확인
5. 라우팅 테이블에 default route 추가
6. DHCP 서버의 Router Option 확인

Linux 임시 설정:

```bash
sudo ip route add default via <gateway_ip> dev <interface>
```

NetworkManager 설정:

```bash
sudo nmcli con mod "<connection-name>" ipv4.gateway <gateway_ip>
sudo nmcli con up "<connection-name>"
```

Windows에서는 어댑터 IPv4 설정에서 기본 게이트웨이를 추가한다.

---

### 게이트웨이 ping이 안 될 때

1. IP 주소와 서브넷 마스크 확인
2. 게이트웨이 IP가 같은 대역인지 확인
3. 케이블/Wi-Fi 연결 확인
4. VLAN이 올바른지 확인
5. ARP 테이블 확인
6. 게이트웨이 장비 상태 확인
7. 방화벽이 ICMP를 막는지 확인

명령어:

```bash
ip addr
ip route
ip neigh
ping <gateway_ip>
```

Windows:

```cmd
ipconfig /all
arp -a
ping <gateway_ip>
```

---

### 게이트웨이는 되는데 외부 IP가 안 될 때

1. default route 확인
2. 게이트웨이 장비의 WAN 상태 확인
3. NAT 설정 확인
4. 게이트웨이 방화벽 확인
5. 상위 라우터 또는 ISP 연결 확인
6. traceroute로 어느 지점에서 끊기는지 확인

명령어:

```bash
ip route
ping <gateway_ip>
ping 8.8.8.8
traceroute 8.8.8.8
```

OpenWrt:

```sh
ifstatus wan
ip route
uci show firewall
ping 8.8.8.8
```

---

### 특정 네트워크 대역만 안 될 때

1. 목적지 대역 route 확인
2. `ip route get`으로 실제 나가는 경로 확인
3. VPN route 여부 확인
4. static route 추가 여부 확인
5. 상대방 return route 확인
6. 방화벽/ACL 확인
7. overlapping subnet 확인

Linux:

```bash
ip route get <destination_ip>
traceroute <destination_ip>
```

Windows:

```cmd
route print
tracert <destination_ip>
```

route 추가 예시:

```bash
sudo ip route add 10.10.20.0/24 via 192.168.1.1
```

---

### VLAN 간 통신이 안 될 때

1. 각 VLAN의 gateway 확인
2. 클라이언트가 올바른 VLAN에 있는지 확인
3. access port VLAN 확인
4. trunk 허용 VLAN 확인
5. L3 SVI 상태 확인
6. inter-VLAN routing 활성화 여부 확인
7. ACL이 차단하는지 확인
8. 양방향 route 확인

점검 항목:

```text
VLAN 10 gateway ping 가능?
VLAN 20 gateway ping 가능?
VLAN 10 -> VLAN 20 traceroute 경로?
각 VLAN SVI up 상태?
trunk에 VLAN 허용?
ACL 정책?
```

---

### VPN 연결 후 라우팅이 꼬일 때

1. VPN 연결 전후 `ip route` 또는 `route print` 비교
2. default route가 VPN으로 변경되었는지 확인
3. 사내 대역 route가 추가되었는지 확인
4. split tunnel 여부 확인
5. overlapping subnet 여부 확인
6. DNS 문제와 분리
7. 필요 시 VPN 관리자에게 route push 설정 확인 요청

Linux:

```bash
ip route
ip route get 8.8.8.8
ip route get <internal_ip>
```

Windows:

```cmd
route print
tracert <internal_ip>
```

---

### VM에서 인터넷이 안 될 때

1. VM 네트워크 모드 확인
2. NAT/Bridge/Host-only 여부 확인
3. VM 내부 IP 확인
4. VM 내부 default gateway 확인
5. gateway ping 확인
6. 8.8.8.8 ping 확인
7. DNS 확인
8. 호스트 방화벽 또는 가상 네트워크 설정 확인

명령어:

```bash
ip addr
ip route
ping <gateway_ip>
ping 8.8.8.8
```

판단:

```text
Host-only 모드:
인터넷이 기본적으로 안 될 수 있음.

NAT 모드:
가상 NAT gateway와 default route 확인.

Bridge 모드:
실제 LAN의 DHCP/gateway를 받아야 함.
```

---

### 다중 인터페이스에서 경로가 이상할 때

1. 전체 route 확인
2. default route가 여러 개인지 확인
3. metric 확인
4. `ip route get`으로 실제 경로 확인
5. 불필요한 인터페이스 비활성화
6. route metric 조정
7. VPN/가상 어댑터 route 확인

Linux:

```bash
ip route
ip route get 8.8.8.8
```

Windows:

```cmd
route print
```

---

## 에이전트 응답 전략

게이트웨이/라우팅 문제로 의심될 때 에이전트는 바로 "게이트웨이를 바꾸세요"라고 말하면 안 된다. 먼저 IP 설정, 기본 게이트웨이 존재 여부, 게이트웨이 ping, 외부 IP ping, DNS 결과를 순서대로 확인해야 한다.

우선 물어볼 정보:

```text
1. 사용 중인 OS가 Windows인지 Linux인지
2. 유선인지 Wi-Fi인지
3. IP 주소와 서브넷 마스크가 무엇인지
4. 기본 게이트웨이가 설정되어 있는지
5. 같은 LAN 장비로 ping이 되는지
6. 기본 게이트웨이로 ping이 되는지
7. 8.8.8.8로 ping이 되는지
8. google.com으로 ping이 되는지
9. VPN 사용 중인지
10. VM, Docker, WSL, OpenWrt, 공유기 환경인지
11. 특정 대역만 안 되는지 전체 인터넷이 안 되는지
```

우선 요청할 명령어:

Windows:

```cmd
ipconfig /all
route print
ping <gateway_ip>
ping 8.8.8.8
tracert 8.8.8.8
```

Linux:

```bash
ip addr
ip route
ip route get 8.8.8.8
ping <gateway_ip>
ping 8.8.8.8
traceroute 8.8.8.8
```

DNS 구분용:

```bash
ping google.com
nslookup google.com
```

---

## 에이전트 응답 예시

### 예시 1: 내부망은 되는데 인터넷이 안 되는 경우

사용자 입력:

```text
같은 공유기에 있는 PC는 ping 되는데 인터넷이 안 돼
```

에이전트 응답:

```text
같은 LAN 내부 장비로 ping이 된다면 IP 주소, NIC, 스위치 또는 Wi-Fi 연결은 어느 정도 정상일 가능성이 있습니다. 하지만 인터넷이 안 된다면 기본 게이트웨이, default route, NAT, 공유기 WAN 연결 문제를 확인해야 합니다.

먼저 아래 순서로 확인하세요.

Windows:
`ipconfig /all`
`route print`
`ping <기본게이트웨이IP>`
`ping 8.8.8.8`

Linux:
`ip addr`
`ip route`
`ping <기본게이트웨이IP>`
`ping 8.8.8.8`

만약 게이트웨이 ping은 되는데 8.8.8.8 ping이 실패한다면, 내 PC보다는 공유기/라우터의 WAN, NAT, 상위 인터넷 연결 문제일 가능성이 높습니다.
```

---

### 예시 2: 기본 게이트웨이가 없는 경우

사용자 입력:

```text
ip route 했는데 default가 없어
```

에이전트 응답:

```text
`ip route`에 `default via ...` 경로가 없다면 외부 네트워크나 인터넷으로 나갈 기본 경로가 없는 상태입니다. 이 경우 같은 LAN 내부 통신은 가능해도 8.8.8.8 같은 외부 IP로는 통신이 어려울 수 있습니다.

정상 예시는 다음과 같습니다.

`default via 192.168.1.1 dev eth0`

먼저 현재 IP와 인터페이스를 확인하세요.

`ip addr`
`ip route`

DHCP 환경이라면 DHCP 서버가 gateway option을 내려주지 않았을 수 있습니다. NetworkManager 사용 환경에서는 다음으로 DHCP 재설정을 시도할 수 있습니다.

`sudo nmcli con mod "<connection-name>" ipv4.method auto`
`sudo nmcli con up "<connection-name>"`

수동 설정 환경이라면 gateway를 명시적으로 추가해야 합니다.
```

---

### 예시 3: 게이트웨이 ping이 실패하는 경우

사용자 입력:

```text
기본 게이트웨이로 ping이 안 돼
```

에이전트 응답:

```text
기본 게이트웨이 ping이 실패한다면 클라이언트와 게이트웨이 사이의 L2/L3 연결 문제를 먼저 의심해야 합니다. 게이트웨이 IP가 잘못되었거나, 서브넷 마스크가 틀렸거나, VLAN이 다르거나, 게이트웨이 장비가 응답하지 않는 상황일 수 있습니다.

먼저 아래를 확인하세요.

`ip addr`
`ip route`
`ip neigh`
`ping <gateway_ip>`

Windows라면:

`ipconfig /all`
`route print`
`arp -a`
`ping <gateway_ip>`

특히 내 IP가 `192.168.1.10/24`인데 게이트웨이가 `192.168.2.1`처럼 다른 대역이면 일반적인 LAN 환경에서는 잘못된 gateway 설정일 가능성이 큽니다.
```

---

### 예시 4: 8.8.8.8은 안 되고 google.com도 안 되는 경우

사용자 입력:

```text
ping 8.8.8.8도 안 되고 ping google.com도 안 돼
```

에이전트 응답:

```text
8.8.8.8 같은 외부 IP로도 ping이 안 된다면 DNS 이전 단계의 문제일 가능성이 높습니다. 즉, google.com이 안 되는 원인을 DNS로 보기 전에 기본 게이트웨이, default route, NAT, 라우팅 문제를 먼저 확인해야 합니다.

확인 순서는 다음과 같습니다.

1. IP 주소가 정상인지 확인
2. 기본 게이트웨이가 있는지 확인
3. 기본 게이트웨이로 ping이 되는지 확인
4. 라우팅 테이블에 default route가 있는지 확인
5. traceroute로 어느 지점에서 끊기는지 확인

Linux:
`ip addr`
`ip route`
`ping <gateway_ip>`
`traceroute 8.8.8.8`

Windows:
`ipconfig /all`
`route print`
`ping <gateway_ip>`
`tracert 8.8.8.8`
```

---

### 예시 5: 특정 대역만 안 되는 경우

사용자 입력:

```text
인터넷은 되는데 10.10.20.0 대역만 접속이 안 돼
```

에이전트 응답:

```text
인터넷은 되는데 특정 대역만 안 된다면 전체 인터넷 라우팅 문제보다는 해당 목적지 대역에 대한 route, VPN route, static route, 방화벽, return route 문제일 가능성이 큽니다.

Linux라면 다음 명령어로 해당 목적지로 실제 어떤 경로를 사용하는지 확인하세요.

`ip route get 10.10.20.10`
`traceroute 10.10.20.10`

Windows라면:

`route print`
`tracert 10.10.20.10`

만약 해당 대역이 VPN으로 가야 하는데 default gateway로 나가고 있다면 VPN route가 누락된 것입니다. 반대로 요청은 목적지에 도착하지만 응답이 안 온다면 상대 네트워크의 return route 또는 방화벽 문제일 수 있습니다.
```

---

### 예시 6: VPN 연결 후 인터넷이 안 되는 경우

사용자 입력:

```text
VPN 켜면 인터넷이 안 돼
```

에이전트 응답:

```text
VPN 연결 후 인터넷이 안 된다면 VPN이 default route를 가져갔지만 VPN 쪽에서 인터넷으로 나가는 NAT 또는 라우팅이 제대로 되지 않는 상황일 수 있습니다. 또는 VPN 정책상 모든 트래픽을 VPN으로 보내도록 설정되어 있을 수 있습니다.

VPN 연결 전후 라우팅 테이블을 비교해보세요.

Linux:
`ip route`
`ip route get 8.8.8.8`

Windows:
`route print`
`tracert 8.8.8.8`

VPN 연결 후 `0.0.0.0/0` 또는 default route가 VPN 인터페이스로 향하면 full tunnel 방식입니다. 이 상태에서 인터넷이 안 된다면 VPN 서버 측 인터넷 NAT/라우팅 문제이거나 VPN 정책 문제일 가능성이 있습니다.
```

---

### 예시 7: VM에서 인터넷이 안 되는 경우

사용자 입력:

```text
VirtualBox VM에서 인터넷이 안 돼
```

에이전트 응답:

```text
VirtualBox VM의 인터넷 문제는 게이트웨이/라우팅 문제일 수도 있고, VM 네트워크 모드 문제일 수도 있습니다.

먼저 VM의 네트워크 모드가 NAT, Bridge, Host-only 중 무엇인지 확인해야 합니다.

- NAT: VM이 VirtualBox의 NAT 게이트웨이를 통해 외부로 나갑니다.
- Bridge: VM이 실제 LAN에 직접 연결된 장비처럼 동작합니다.
- Host-only: 호스트와 VM 사이의 내부망이라 기본적으로 인터넷이 안 될 수 있습니다.

VM 내부에서 다음을 확인하세요.

`ip addr`
`ip route`
`ping <gateway_ip>`
`ping 8.8.8.8`

만약 default route가 없다면 VM이 게이트웨이를 받지 못한 상태입니다. Host-only 모드라면 인터넷이 안 되는 것이 정상일 수 있고, NAT 또는 Bridge 모드로 바꿔야 할 수 있습니다.
```

---

## 주의할 점

게이트웨이/라우팅 문제를 진단할 때 다음을 주의해야 한다.

1. "인터넷이 안 된다"는 말만 듣고 DNS 문제로 단정하면 안 된다.
2. 8.8.8.8 같은 외부 IP로도 통신이 안 되면 DNS 이전의 gateway/routing 문제를 먼저 확인해야 한다.
3. 같은 LAN 내부 ping 성공은 외부 인터넷 가능을 의미하지 않는다.
4. 기본 게이트웨이가 없으면 일반적으로 외부 네트워크 통신이 어렵다.
5. 기본 게이트웨이는 보통 클라이언트와 같은 네트워크 대역에 있어야 한다.
6. 게이트웨이 ping 실패는 IP, subnet mask, VLAN, ARP, L2 문제와 관련될 수 있다.
7. ping 실패만으로 장비 장애를 단정하면 안 된다. ICMP가 차단될 수 있다.
8. traceroute의 별표(*)는 반드시 장애가 아니라 ICMP 응답 차단일 수 있다.
9. 라우팅은 왕복 경로가 중요하다. return route가 없으면 통신이 실패한다.
10. NAT가 필요한 환경에서 NAT가 없으면 사설 IP는 인터넷과 정상 통신하기 어렵다.
11. VPN은 라우팅 테이블을 크게 변경할 수 있다.
12. 다중 인터페이스 환경에서는 metric 때문에 예상과 다른 경로로 나갈 수 있다.
13. VirtualBox Host-only 네트워크는 기본적으로 인터넷용이 아니다.
14. Docker, WSL, VM 어댑터가 실제 네트워크 route와 충돌할 수 있다.
15. 특정 대역만 안 되면 default gateway보다 static route, VPN route, ACL, return route를 확인해야 한다.
16. VLAN 간 통신은 L2 스위칭만으로 되지 않고 inter-VLAN routing이 필요하다.
17. 서브넷 마스크 오류는 일부 통신만 이상하게 만드는 원인이 될 수 있다.
18. 게이트웨이 장비 자체의 WAN, NAT, firewall 상태도 확인해야 한다.
19. DHCP로 받은 gateway가 잘못되면 DHCP 문서도 함께 참고해야 한다.
20. 8.8.8.8은 되는데 google.com만 안 되면 gateway/routing보다 DNS 문서를 참고해야 한다.

---

## 빠른 진단 요약

```text
1. ipconfig /all 또는 ip addr로 IP 주소 확인
2. 서브넷 마스크/prefix 확인
3. 기본 게이트웨이 존재 여부 확인
4. ip route 또는 route print로 default route 확인
5. ping <gateway_ip>로 게이트웨이 도달성 확인
6. ping 8.8.8.8로 외부 IP 통신 확인
7. ping google.com 또는 nslookup으로 DNS 문제와 구분
8. traceroute/tracert로 어느 홉에서 끊기는지 확인
9. ip route get <destination_ip>로 특정 목적지 경로 확인
10. VPN, VM, Docker, WSL 등 가상 인터페이스 확인
11. 다중 default route와 metric 확인
12. VLAN 간 통신이면 SVI, trunk, ACL 확인
13. 공유기/라우터의 WAN, NAT, firewall 확인
14. 필요 시 tcpdump로 패킷이 어느 인터페이스로 나가는지 확인
```

---

## 핵심 키워드

Gateway, Routing, Gateway Troubleshooting, Routing Troubleshooting, 기본 게이트웨이, default gateway, default route, ip route, route print, ip route get, traceroute, tracert, tracepath, ping gateway, ping 8.8.8.8, LAN은 되는데 인터넷 안 됨, 내부망은 되는데 외부망 안 됨, 같은 네트워크 통신, 외부 네트워크 통신, 라우팅 테이블, next hop, metric, static route, default via, 0.0.0.0/0, gateway 없음, default route 없음, gateway ping 실패, 외부 IP ping 실패, DNS와 구분, 서브넷 마스크 오류, subnet mask, prefix, ARP, ip neigh, arp -a, VLAN routing, inter-VLAN routing, L3 switch, SVI, router on a stick, trunk, access VLAN, ACL, NAT, masquerade, OpenWrt routing, WAN, LAN, firewall zone, return route, asymmetric routing, overlapping subnet, VPN routing, split tunnel, full tunnel, 다중 인터페이스, route metric, VirtualBox NAT, Bridge, Host-only, VMware, WSL, Docker bridge, Tailscale, ZeroTier.