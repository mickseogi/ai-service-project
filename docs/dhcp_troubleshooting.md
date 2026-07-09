# DHCP Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 DHCP 관련 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

DHCP 문제는 사용자가 단순히 "인터넷이 안 된다", "IP가 안 잡힌다", "와이파이는 연결됐는데 인터넷이 안 된다"처럼 표현하는 경우가 많다. 실제 원인은 DHCP 서버 장애, IP 풀 고갈, VLAN/라우팅 문제, DHCP Relay 누락, 잘못된 DHCP 서버, 클라이언트 네트워크 어댑터 문제, 가상머신 네트워크 모드 문제 등 다양하다.

에이전트는 사용자의 증상을 듣고 먼저 다음을 구분해야 한다.

- IP 주소를 아예 받지 못한 문제인지
- IP는 받았지만 게이트웨이 또는 DNS 정보가 잘못된 문제인지
- DHCP 서버가 응답하지 않는 문제인지
- DHCP 서버는 응답하지만 잘못된 정보를 배포하는 문제인지
- 같은 네트워크 내부 문제인지
- 외부 인터넷 연결 문제인지
- DHCP 문제가 아니라 DNS, Gateway, Routing, Firewall 문제인지

DHCP 문제를 정확히 판단하려면 `IP 주소`, `서브넷 마스크`, `기본 게이트웨이`, `DNS 서버`, `DHCP 서버 주소`, `임대 시간`, `네트워크 인터페이스 상태`를 함께 확인해야 한다.

---

## 관련 사용자 표현

사용자는 DHCP라는 용어를 직접 말하지 않을 수도 있다. 다음과 같은 표현은 DHCP 문제와 관련될 가능성이 있다.

- 인터넷이 안 돼
- 와이파이는 연결됐는데 인터넷이 안 돼
- 랜선은 꽂았는데 네트워크가 안 돼
- IP가 안 잡혀
- IP 주소를 못 받아와
- 자동 IP 할당이 안 돼
- 169.254로 시작하는 IP가 떠
- 게이트웨이가 없어
- 기본 게이트웨이가 비어 있어
- DNS가 이상하게 잡혀
- 같은 공유기에 연결된 다른 기기는 되는데 내 컴퓨터만 안 돼
- VM에서 IP를 못 받아와
- VirtualBox에서 인터넷이 안 돼
- NAT로 했는데 IP가 안 잡혀
- Bridge로 했는데 IP가 안 잡혀
- DHCP 서버를 만들었는데 클라이언트가 IP를 못 받아
- DHCP Discover는 보이는데 Offer가 안 와
- DHCP 서버 로그에 요청이 안 찍혀
- OpenWrt에서 DHCP lease가 안 보여
- 리눅스에서 `ip addr` 했는데 IP가 없어
- Windows에서 `ipconfig` 했는데 이상한 주소가 나와
- 네트워크 연결됨이라고 뜨는데 인터넷 없음이라고 나와

---

## 핵심 개념

DHCP는 Dynamic Host Configuration Protocol의 약자이며, 클라이언트가 네트워크에 접속했을 때 필요한 IP 설정 정보를 자동으로 할당받기 위한 프로토콜이다.

DHCP를 통해 일반적으로 다음 정보를 받는다.

- IP 주소
- 서브넷 마스크
- 기본 게이트웨이
- DNS 서버
- 도메인 이름
- 임대 시간
- DHCP 서버 주소
- 기타 네트워크 옵션

DHCP가 정상 동작하지 않으면 클라이언트는 네트워크에 연결되어 있어도 올바른 IP 설정을 받지 못한다. 이 경우 같은 LAN 내부 통신, 게이트웨이 통신, 인터넷 접속, DNS 조회 등이 실패할 수 있다.

DHCP는 보통 다음 환경에서 사용된다.

- 가정용 공유기
- 회사 네트워크
- 학교 네트워크
- 사무실 네트워크
- Wi-Fi AP
- OpenWrt 라우터
- Windows Server DHCP
- Linux DHCP 서버
- Kea DHCP 서버
- dnsmasq
- 가상머신 NAT 네트워크
- VirtualBox Host-only 네트워크
- VMware NAT/Bridge 네트워크

---

## DHCP 정상 동작 흐름

DHCP의 기본 동작은 DORA 과정으로 설명할 수 있다.

### 1. DHCP Discover

클라이언트가 네트워크에 처음 연결되면 자신에게 IP 주소가 없으므로 DHCP 서버를 찾기 위해 브로드캐스트 패킷을 보낸다.

- 출발지 IP: `0.0.0.0`
- 목적지 IP: `255.255.255.255`
- 클라이언트 포트: UDP 68
- 서버 포트: UDP 67

이 단계에서 클라이언트는 "이 네트워크에 DHCP 서버가 있으면 응답해 달라"고 요청한다.

### 2. DHCP Offer

DHCP 서버가 Discover를 받으면 사용 가능한 IP 주소와 네트워크 설정 정보를 클라이언트에게 제안한다.

Offer에는 보통 다음 정보가 포함된다.

- 제안할 IP 주소
- 서브넷 마스크
- 기본 게이트웨이
- DNS 서버
- 임대 시간
- DHCP 서버 식별자

### 3. DHCP Request

클라이언트는 받은 Offer 중 하나를 선택하여 해당 DHCP 서버에 IP 주소를 사용하겠다고 요청한다.

클라이언트가 여러 DHCP 서버로부터 Offer를 받을 수도 있다. 이 경우 하나의 DHCP 서버를 선택하고, 다른 DHCP 서버의 제안은 사용하지 않는다.

### 4. DHCP ACK

DHCP 서버는 클라이언트의 Request를 승인하고 ACK를 보낸다. 이 시점부터 클라이언트는 해당 IP 주소를 사용할 수 있다.

정상 흐름은 다음과 같다.

```text
Client -> DHCP Discover -> Network
DHCP Server -> DHCP Offer -> Client
Client -> DHCP Request -> DHCP Server
DHCP Server -> DHCP ACK -> Client
```

이 과정 중 하나라도 실패하면 클라이언트는 정상적인 IP 설정을 받지 못한다.

---

## DHCP에서 사용하는 포트

DHCP는 UDP 기반 프로토콜이다.

```text
DHCP Server: UDP 67
DHCP Client: UDP 68
```

방화벽, 보안 장비, ACL, 스위치 보안 설정, 가상 네트워크 설정에서 UDP 67/68이 차단되면 DHCP가 실패할 수 있다.

특히 DHCP Discover는 브로드캐스트로 전달되기 때문에, 같은 브로드캐스트 도메인 안에 DHCP 서버가 없거나 DHCP Relay가 없으면 다른 네트워크의 DHCP 서버까지 도달하지 못한다.

---

## DHCP와 브로드캐스트 도메인

DHCP Discover는 기본적으로 브로드캐스트 패킷이다.

브로드캐스트는 라우터를 넘어가지 않는다. 따라서 클라이언트와 DHCP 서버가 서로 다른 네트워크 또는 다른 VLAN에 있다면, DHCP 요청은 기본적으로 서버에 도달하지 못한다.

이때 필요한 것이 DHCP Relay이다.

### DHCP Relay가 필요한 상황

- 클라이언트는 VLAN 10에 있음
- DHCP 서버는 VLAN 20 또는 서버망에 있음
- 클라이언트의 DHCP Discover는 VLAN 10 안에서만 브로드캐스트됨
- 라우터 또는 L3 스위치가 DHCP Relay 역할을 해야 DHCP 서버로 요청을 전달할 수 있음

즉, 서로 다른 VLAN에서 중앙 DHCP 서버를 사용할 경우 DHCP Relay 설정이 필요하다.

Cisco 계열 장비에서는 보통 다음과 같은 설정이 사용된다.

```text
ip helper-address <DHCP_SERVER_IP>
```

DHCP Relay가 없으면 클라이언트는 IP를 받지 못하고, Windows에서는 169.254.x.x 주소가 잡힐 수 있다.

---

## APIPA와 169.254.x.x 주소

Windows 클라이언트에서 DHCP 서버로부터 IP 주소를 받지 못하면 APIPA 주소가 자동으로 할당될 수 있다.

APIPA는 Automatic Private IP Addressing의 약자이다.

대표 주소 범위는 다음과 같다.

```text
169.254.0.0/16
```

예시:

```text
169.254.12.34
255.255.0.0
```

이 주소가 보이면 보통 다음 의미로 해석할 수 있다.

- DHCP 서버로부터 정상적인 IP를 받지 못했다.
- DHCP Discover에 대한 Offer를 받지 못했다.
- 네트워크에는 연결되어 있지만 IP 자동 할당이 실패했다.
- 같은 APIPA 대역끼리는 제한적으로 통신할 수 있지만, 일반적인 게이트웨이/인터넷 통신은 어렵다.

주의할 점은 169.254.x.x가 보인다고 해서 항상 DHCP 서버 자체가 죽었다고 단정하면 안 된다. 중간 네트워크, VLAN, 스위치, 방화벽, 무선 인증, 가상 네트워크 설정 문제일 수도 있다.

---

## DHCP 문제의 대표 증상

### 1. IP 주소가 169.254.x.x로 설정됨

가장 전형적인 DHCP 실패 증상이다.

가능한 원인:

- DHCP 서버가 꺼져 있음
- DHCP 서비스 장애
- DHCP 서버와 클라이언트가 다른 VLAN에 있음
- DHCP Relay 누락
- DHCP IP 풀 고갈
- 클라이언트 네트워크 어댑터 문제
- 케이블 또는 Wi-Fi 연결 문제
- 방화벽 또는 보안 장비가 UDP 67/68 차단
- 가상머신 네트워크 모드 문제

### 2. IP 주소가 아예 없음

Linux에서 `ip addr` 명령을 실행했을 때 인터페이스에 IPv4 주소가 없을 수 있다.

가능한 원인:

- 인터페이스가 down 상태
- NetworkManager가 해당 인터페이스를 관리하지 않음
- DHCP 클라이언트가 실행되지 않음
- 네트워크 프로파일이 static으로 잘못 설정됨
- DHCP 요청이 실패함
- 가상 NIC가 연결되지 않음

### 3. IP는 있지만 인터넷이 안 됨

이 경우 DHCP가 일부만 정상 동작했거나, DHCP 문제처럼 보이지만 실제로는 Gateway, Routing, DNS 문제가 원인일 수 있다.

확인할 항목:

- IP 주소가 정상 사설 IP인지
- 서브넷 마스크가 올바른지
- 기본 게이트웨이가 존재하는지
- DNS 서버가 존재하는지
- 게이트웨이로 ping이 되는지
- 8.8.8.8로 ping이 되는지
- google.com 같은 도메인으로 ping이 되는지

판단 기준:

```text
게이트웨이 ping 실패 -> 내부 네트워크, L2/L3, 게이트웨이 문제 가능성
8.8.8.8 ping 성공 + google.com 실패 -> DNS 문제 가능성
IP 있음 + 게이트웨이 없음 -> DHCP 옵션 누락 또는 잘못된 설정 가능성
IP 있음 + DNS 없음 -> DHCP DNS 옵션 문제 가능성
```

### 4. 같은 네트워크의 다른 장비는 정상인데 특정 장비만 안 됨

이 경우 DHCP 서버 전체 장애보다는 특정 클라이언트 문제일 가능성이 높다.

가능한 원인:

- 해당 PC의 네트워크 어댑터 문제
- 잘못된 static IP 설정
- DHCP 사용 안 함
- MAC 주소 기반 차단
- 포트 보안 설정
- 무선 인증 실패
- 드라이버 문제
- OS 네트워크 스택 문제
- 가상 어댑터 우선순위 문제
- VPN 또는 보안 프로그램 영향

### 5. 여러 장비가 동시에 IP를 못 받음

이 경우 DHCP 서버 또는 네트워크 인프라 문제일 가능성이 높다.

가능한 원인:

- DHCP 서버 장애
- 공유기 DHCP 기능 꺼짐
- DHCP IP 풀 고갈
- 스위치 장애
- VLAN trunk 문제
- DHCP Relay 문제
- 라우터/L3 스위치 설정 문제
- 중앙 DHCP 서버와의 경로 문제
- 보안 장비에서 DHCP 차단

### 6. IP는 받았지만 대역이 이상함

예를 들어 회사 네트워크에서는 10.10.10.x를 받아야 하는데 192.168.0.x를 받는 경우가 있다.

가능한 원인:

- 잘못된 DHCP 서버가 응답함
- Rogue DHCP 서버 존재
- 개인 공유기가 네트워크에 연결됨
- VM NAT 네트워크의 DHCP를 받은 상태
- Wi-Fi가 다른 SSID에 연결됨
- Bridge 대상 인터페이스가 잘못됨
- VLAN 할당이 잘못됨

이 경우 DHCP 서버 주소를 반드시 확인해야 한다.

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
nmcli dev show
```

또는 DHCP lease 파일을 확인한다.

---

## Possible Causes

DHCP 문제의 원인은 크게 서버 측, 클라이언트 측, 네트워크 경로 측, 보안 설정 측, 가상화 환경 측으로 나눌 수 있다.

---

### 1. DHCP 서버가 동작하지 않음

DHCP 서버 프로세스가 꺼져 있으면 클라이언트는 IP를 받을 수 없다.

Linux에서 DHCP 서버로 사용하는 서비스는 환경에 따라 다르다.

예시:

- `dhcpd`
- `kea-dhcp4-server`
- `dnsmasq`
- `isc-dhcp-server`
- OpenWrt의 `dnsmasq`
- Windows Server DHCP

확인 명령어 예시:

```bash
systemctl status dhcpd
systemctl status kea-dhcp4-server
systemctl status dnsmasq
systemctl status isc-dhcp-server
```

서비스가 꺼져 있다면 시작한다.

```bash
sudo systemctl start dhcpd
sudo systemctl enable dhcpd
```

또는 Kea 사용 시:

```bash
sudo systemctl start kea-dhcp4-server
sudo systemctl enable kea-dhcp4-server
```

OpenWrt에서는 보통 dnsmasq가 DHCP 역할을 한다.

```sh
/etc/init.d/dnsmasq status
/etc/init.d/dnsmasq restart
```

---

### 2. DHCP IP 풀 고갈

DHCP 서버가 정상 동작해도 할당 가능한 IP 주소가 남아 있지 않으면 새 클라이언트는 IP를 받을 수 없다.

예시:

```text
DHCP Pool: 192.168.1.100 ~ 192.168.1.150
사용 가능한 주소 수: 51개
현재 연결 장비 수: 51개 이상
```

이 경우 새 장비는 DHCP Offer를 받지 못하거나, 서버 로그에 할당 가능한 주소가 없다는 메시지가 남을 수 있다.

확인할 항목:

- DHCP pool 범위
- 현재 lease 목록
- 만료되지 않은 lease 수
- 예약 IP 개수
- 제외 주소 범위
- 중복 IP 여부

OpenWrt에서 lease 확인:

```sh
cat /tmp/dhcp.leases
```

Linux DHCP 서버 로그 확인:

```bash
journalctl -u dhcpd --no-pager
journalctl -u kea-dhcp4-server --no-pager
journalctl -u dnsmasq --no-pager
```

---

### 3. 클라이언트와 DHCP 서버가 같은 네트워크에 있지 않음

DHCP Discover는 브로드캐스트이므로 기본적으로 라우터를 넘지 못한다.

따라서 다음 구조에서는 DHCP Relay가 필요하다.

```text
Client VLAN 10 -> L3 Switch/Router -> DHCP Server VLAN 20
```

DHCP Relay가 없으면 클라이언트의 Discover가 DHCP 서버까지 전달되지 않는다.

판단 기준:

- 같은 VLAN의 클라이언트는 IP를 받음
- 다른 VLAN의 클라이언트만 IP를 못 받음
- DHCP 서버는 정상 동작 중
- 서버 로그에 해당 VLAN 클라이언트의 Discover가 보이지 않음

해결:

- 라우터 또는 L3 스위치에 DHCP Relay 설정
- VLAN 인터페이스에 helper address 설정
- DHCP 서버에 해당 서브넷 scope 추가
- VLAN trunk 설정 확인

---

### 4. DHCP Scope 또는 Subnet 설정 오류

DHCP 서버에는 네트워크 대역별로 scope가 설정되어 있어야 한다.

예를 들어 클라이언트 네트워크가 `192.168.10.0/24`인데 DHCP 서버에는 `192.168.20.0/24` scope만 있다면 올바른 IP를 할당할 수 없다.

확인할 항목:

- DHCP scope 네트워크 주소
- 서브넷 마스크
- 할당 범위
- 제외 범위
- 기본 게이트웨이 옵션
- DNS 옵션
- DHCP Relay가 전달한 giaddr 정보
- 서버가 해당 subnet을 인식하는지

---

### 5. 기본 게이트웨이 옵션 누락

DHCP로 IP 주소는 받았지만 기본 게이트웨이가 없으면 외부 네트워크로 나갈 수 없다.

DHCP에서 기본 게이트웨이는 보통 Router Option으로 전달된다.

대표 옵션:

```text
Option 3: Router / Default Gateway
```

증상:

- IP 주소는 정상으로 보임
- 같은 LAN 내부 통신은 가능
- 외부 인터넷 통신은 불가능
- `ip route` 또는 `route print`에서 default route가 없음

Windows 확인:

```cmd
ipconfig /all
route print
```

Linux 확인:

```bash
ip addr
ip route
```

정상적인 Linux 기본 라우트 예시:

```text
default via 192.168.1.1 dev eth0
```

기본 라우트가 없다면 DHCP 서버의 gateway/router option을 확인해야 한다.

---

### 6. DNS 옵션 누락 또는 잘못된 DNS 서버 배포

DHCP는 DNS 서버 정보도 함께 전달할 수 있다.

대표 옵션:

```text
Option 6: DNS Server
```

DNS 옵션이 없거나 잘못되면 IP 통신은 되지만 도메인 접속이 실패할 수 있다.

대표 증상:

```text
ping 8.8.8.8 성공
ping google.com 실패
웹사이트 주소 접속 실패
```

이 경우 DHCP 문제와 DNS 문제를 함께 봐야 한다.

확인 명령어:

Windows:

```cmd
ipconfig /all
nslookup google.com
```

Linux:

```bash
resolvectl status
cat /etc/resolv.conf
nslookup google.com
dig google.com
```

판단 기준:

- IP 주소 정상
- 게이트웨이 정상
- 외부 IP ping 성공
- 도메인 조회 실패

이면 DHCP의 DNS 옵션 문제 또는 DNS 서버 자체 문제일 가능성이 높다.

---

### 7. 잘못된 DHCP 서버 또는 Rogue DHCP

네트워크 안에 의도하지 않은 DHCP 서버가 존재하면 클라이언트가 잘못된 IP 설정을 받을 수 있다.

예시:

- 개인 공유기를 회사 LAN에 연결
- 노트북 인터넷 공유 기능 활성화
- 가상머신 NAT DHCP가 물리망에 영향을 줌
- 테스트용 DHCP 서버가 운영망에 연결됨
- OpenWrt 라우터 DHCP가 의도치 않게 활성화됨

증상:

- IP 대역이 원래 네트워크와 다름
- 기본 게이트웨이가 이상함
- DNS 서버가 이상함
- 같은 자리에 있는 장비마다 다른 대역을 받음
- DHCP 서버 주소가 예상과 다름

확인:

Windows:

```cmd
ipconfig /all
```

확인해야 할 항목:

```text
DHCP Server . . . . . . . . . . . : <서버 주소>
Default Gateway . . . . . . . . . : <게이트웨이 주소>
DNS Servers . . . . . . . . . . . : <DNS 주소>
```

Linux:

```bash
nmcli dev show
```

확인해야 할 항목:

```text
IP4.DHCP_SERVER
IP4.GATEWAY
IP4.DNS
```

해결:

- Rogue DHCP 서버 제거
- 불필요한 공유기 DHCP 비활성화
- 스위치에서 DHCP Snooping 적용
- 신뢰할 수 있는 포트만 DHCP 서버 응답 허용
- 운영망과 테스트망 분리

---

### 8. VLAN 설정 문제

VLAN 환경에서는 DHCP 문제가 자주 발생한다.

가능한 원인:

- 클라이언트 포트가 잘못된 VLAN에 할당됨
- trunk 포트에서 해당 VLAN이 허용되지 않음
- native VLAN 불일치
- L3 SVI가 down 상태
- DHCP Relay가 해당 VLAN 인터페이스에 설정되지 않음
- DHCP 서버에 해당 VLAN 대역 scope가 없음

판단 기준:

- 특정 VLAN 사용자만 IP를 못 받음
- 다른 VLAN은 정상
- 같은 스위치의 다른 포트에서는 정상
- 포트 VLAN 변경 후 문제가 발생
- 새 VLAN 생성 후 DHCP만 안 됨

진단 순서:

1. 클라이언트 포트의 access VLAN 확인
2. trunk에 해당 VLAN이 허용되는지 확인
3. VLAN 인터페이스/SVI 상태 확인
4. DHCP Relay 설정 확인
5. DHCP 서버 scope 확인
6. 서버 로그에서 Discover 수신 여부 확인

---

### 9. 방화벽 또는 ACL이 DHCP를 차단

DHCP는 UDP 67/68을 사용한다.

방화벽, ACL, 보안 장비가 DHCP 트래픽을 차단하면 IP 할당이 실패할 수 있다.

특히 다음 구간을 확인해야 한다.

- 클라이언트 로컬 방화벽
- Linux 서버 firewalld
- Windows 방화벽
- 라우터 ACL
- L3 스위치 ACL
- 보안 장비 정책
- 클라우드 보안 그룹
- 가상 네트워크 필터링

Linux firewalld 확인:

```bash
sudo firewall-cmd --list-all
```

DHCP 서비스 허용 예시:

```bash
sudo firewall-cmd --add-service=dhcp --permanent
sudo firewall-cmd --reload
```

단, 실제 운영 환경에서는 무조건 방화벽을 끄기보다 필요한 DHCP 트래픽만 허용하는 것이 좋다.

---

### 10. 클라이언트 네트워크 설정 문제

클라이언트가 DHCP를 사용하도록 설정되어 있지 않으면 IP를 자동으로 받을 수 없다.

Windows에서 확인할 항목:

- IPv4 설정이 자동 IP 받기로 되어 있는지
- 수동 IP가 설정되어 있지 않은지
- 잘못된 DNS가 고정되어 있지 않은지
- VPN 어댑터가 우선순위를 가져가지 않는지
- 네트워크 어댑터가 사용 안 함 상태가 아닌지

Linux에서 확인할 항목:

- NetworkManager 프로파일이 DHCP인지
- 인터페이스가 up 상태인지
- netplan 설정이 DHCP인지
- systemd-networkd 설정이 DHCP인지
- static IP가 잘못 설정되어 있지 않은지

Linux NetworkManager 확인:

```bash
nmcli con show
nmcli dev status
nmcli dev show
```

특정 연결의 IPv4 방식 확인:

```bash
nmcli con show "<connection-name>" | grep ipv4.method
```

DHCP로 설정:

```bash
sudo nmcli con mod "<connection-name>" ipv4.method auto
sudo nmcli con up "<connection-name>"
```

---

### 11. 가상머신 네트워크 모드 문제

VirtualBox, VMware, Hyper-V, WSL 등에서는 네트워크 모드에 따라 DHCP 동작이 달라진다.

대표 모드:

- NAT
- Bridge
- Host-only
- Internal Network
- NAT Network

각 모드의 의미:

```text
NAT:
가상머신이 호스트를 통해 외부로 나감. 보통 가상화 프로그램 내부 DHCP가 IP를 할당함.

Bridge:
가상머신이 실제 LAN에 직접 연결된 것처럼 동작함. 실제 공유기나 네트워크의 DHCP 서버에서 IP를 받음.

Host-only:
호스트와 가상머신 사이의 전용 네트워크. 외부 인터넷은 기본적으로 안 될 수 있음. Host-only DHCP 서버가 IP를 줄 수 있음.

Internal Network:
가상머신끼리만 통신하는 내부망. DHCP 서버가 따로 없으면 IP를 못 받을 수 있음.
```

VM에서 IP를 못 받는 경우 확인할 항목:

- VM 네트워크 어댑터가 연결됨 상태인지
- NAT/Bridge/Host-only 중 어떤 모드인지
- Bridge 대상 물리 인터페이스가 올바른지
- Host-only DHCP 서버가 켜져 있는지
- VM 내부 OS에서 인터페이스가 up인지
- VM 내부 OS가 DHCP를 사용하도록 설정되어 있는지
- 호스트 방화벽이 가상 네트워크를 막지 않는지

VirtualBox에서 자주 발생하는 문제:

- Bridge 대상이 Wi-Fi가 아니라 다른 어댑터로 잡힘
- Host-only 네트워크에는 인터넷이 없는데 인터넷이 안 된다고 착각함
- NAT에서는 외부 접속은 되지만 외부에서 VM으로 접속하려면 포트포워딩이 필요함
- Internal Network에는 DHCP 서버가 없어서 IP가 안 잡힘

---

## Recommended Commands

DHCP 문제는 운영체제별로 확인 명령어가 다르다.

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
DHCP Enabled
DHCP Server
DNS Servers
Lease Obtained
Lease Expires
```

판단 기준:

```text
DHCP Enabled: Yes
IPv4 Address: 169.254.x.x -> DHCP 실패 가능성
Default Gateway 없음 -> 외부 통신 불가 가능성
DHCP Server가 예상과 다름 -> Rogue DHCP 가능성
DNS Servers 없음 -> 도메인 조회 실패 가능성
```

### DHCP 임대 해제

```cmd
ipconfig /release
```

### DHCP 재요청

```cmd
ipconfig /renew
```

### DNS 캐시 초기화

```cmd
ipconfig /flushdns
```

### 라우팅 테이블 확인

```cmd
route print
```

### 게이트웨이 통신 확인

```cmd
ping <default_gateway_ip>
```

### 외부 IP 통신 확인

```cmd
ping 8.8.8.8
```

### DNS 동작 확인

```cmd
nslookup google.com
```

---

## Linux 클라이언트 진단 명령어

### 인터페이스와 IP 주소 확인

```bash
ip addr
```

또는 축약:

```bash
ip a
```

확인할 항목:

```text
인터페이스가 UP인지
IPv4 주소가 있는지
169.254.x.x 주소인지
예상한 대역의 IP인지
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
잘못된 gateway
다른 인터페이스가 default route를 가져감
```

### NetworkManager 상태 확인

```bash
nmcli dev status
```

### NetworkManager 상세 정보 확인

```bash
nmcli dev show
```

확인할 항목:

```text
IP4.ADDRESS
IP4.GATEWAY
IP4.DNS
IP4.DHCP_SERVER
```

### 특정 연결 정보 확인

```bash
nmcli con show
nmcli con show "<connection-name>"
```

### DHCP로 설정 변경

```bash
sudo nmcli con mod "<connection-name>" ipv4.method auto
sudo nmcli con up "<connection-name>"
```

### NetworkManager 로그 확인

```bash
journalctl -u NetworkManager --no-pager
```

최근 로그만 확인:

```bash
journalctl -u NetworkManager -n 100 --no-pager
```

### DHCP 클라이언트 직접 실행

환경에 따라 `dhclient`가 설치되어 있을 수 있다.

```bash
sudo dhclient -v <interface>
```

예시:

```bash
sudo dhclient -v eth0
sudo dhclient -v ens33
sudo dhclient -v enp0s3
```

`dhclient -v`는 DHCP Discover, Offer, Request, ACK 흐름을 비교적 직접적으로 확인하는 데 유용하다.

### 인터페이스 down/up

```bash
sudo ip link set <interface> down
sudo ip link set <interface> up
```

NetworkManager 사용 시:

```bash
sudo nmcli dev disconnect <interface>
sudo nmcli dev connect <interface>
```

---

## Linux DHCP 서버 진단 명령어

### DHCP 서버 서비스 상태 확인

```bash
systemctl status dhcpd
systemctl status kea-dhcp4-server
systemctl status dnsmasq
systemctl status isc-dhcp-server
```

### DHCP 서버 로그 확인

```bash
journalctl -u dhcpd --no-pager
journalctl -u kea-dhcp4-server --no-pager
journalctl -u dnsmasq --no-pager
journalctl -u isc-dhcp-server --no-pager
```

### DHCP 서버가 포트를 열고 있는지 확인

```bash
sudo ss -lunp | grep ':67'
```

또는:

```bash
sudo netstat -lunp | grep ':67'
```

정상적으로 DHCP 서버가 실행 중이면 UDP 67 포트를 사용 중인 프로세스가 보여야 한다.

### 방화벽 확인

```bash
sudo firewall-cmd --list-all
```

DHCP 허용:

```bash
sudo firewall-cmd --add-service=dhcp --permanent
sudo firewall-cmd --reload
```

---

## OpenWrt DHCP 진단 명령어

OpenWrt에서는 보통 `dnsmasq`가 DHCP 서버 역할을 한다.

### DHCP lease 확인

```sh
cat /tmp/dhcp.leases
```

출력에는 보통 다음 정보가 포함된다.

```text
만료 시간
MAC 주소
할당된 IP 주소
호스트 이름
클라이언트 ID
```

### dnsmasq 상태 확인

```sh
/etc/init.d/dnsmasq status
```

### dnsmasq 재시작

```sh
/etc/init.d/dnsmasq restart
```

### 네트워크 설정 확인

```sh
uci show network
uci show dhcp
```

### LAN 인터페이스 확인

```sh
ip addr
ip route
```

### 로그 확인

```sh
logread | grep dnsmasq
logread | grep DHCP
```

OpenWrt에서 클라이언트가 IP를 못 받는 경우 다음을 확인한다.

- LAN 인터페이스가 올바른 IP를 가지고 있는지
- DHCP 서버가 LAN 인터페이스에 활성화되어 있는지
- ignore 옵션이 1로 되어 있지 않은지
- IP pool 시작 주소와 개수가 적절한지
- 클라이언트가 LAN 포트 또는 올바른 Wi-Fi SSID에 연결되어 있는지
- WAN과 LAN 포트를 혼동하지 않았는지

---

## Packet Capture로 DHCP 확인

명령어 출력만으로 부족하면 패킷 캡처를 통해 DHCP Discover/Offer가 실제로 오가는지 확인할 수 있다.

### Linux tcpdump

```bash
sudo tcpdump -i <interface> -n port 67 or port 68
```

예시:

```bash
sudo tcpdump -i eth0 -n port 67 or port 68
```

정상 흐름에서는 다음과 유사한 패킷이 보여야 한다.

```text
DHCP Discover
DHCP Offer
DHCP Request
DHCP ACK
```

### 판단 기준

```text
Discover가 안 보임:
클라이언트가 DHCP 요청을 보내지 않거나 인터페이스 문제일 수 있음.

Discover는 보이지만 Offer가 안 보임:
DHCP 서버가 응답하지 않거나, 서버까지 요청이 도달하지 않거나, 서버가 줄 IP가 없을 수 있음.

Offer는 보이지만 Request/ACK가 없음:
클라이언트가 제안을 수락하지 못하거나 중간에서 응답이 손실될 수 있음.

ACK까지 보이는데 IP가 설정되지 않음:
클라이언트 OS 네트워크 설정, NetworkManager, 드라이버, 보안 프로그램 문제일 수 있음.
```

---

## 단계별 진단 절차

DHCP 문제는 다음 순서로 진단하는 것이 좋다.

### 1단계: 현재 IP 설정 확인

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
ip addr
ip route
nmcli dev show
```

확인할 것:

- IPv4 주소가 있는가?
- 169.254.x.x인가?
- 예상한 네트워크 대역인가?
- 서브넷 마스크가 맞는가?
- 기본 게이트웨이가 있는가?
- DNS 서버가 있는가?
- DHCP 서버 주소가 예상한 서버인가?

### 2단계: 인터페이스 상태 확인

Linux:

```bash
ip link
nmcli dev status
```

확인할 것:

- 인터페이스가 UP인가?
- 케이블이 연결되어 있는가?
- Wi-Fi가 연결되어 있는가?
- 올바른 SSID에 연결되어 있는가?
- VM이라면 가상 NIC가 connected 상태인가?

### 3단계: DHCP 재요청

Windows:

```cmd
ipconfig /release
ipconfig /renew
```

Linux:

```bash
sudo nmcli dev disconnect <interface>
sudo nmcli dev connect <interface>
```

또는:

```bash
sudo dhclient -v <interface>
```

### 4단계: 게이트웨이 통신 확인

게이트웨이가 있다면 ping으로 확인한다.

```bash
ping <gateway_ip>
```

판단 기준:

```text
게이트웨이 ping 성공:
L2/L3 내부 연결은 대체로 정상일 가능성이 있음.

게이트웨이 ping 실패:
같은 LAN 내부 연결 문제, VLAN 문제, 게이트웨이 장애, 방화벽, 잘못된 IP 대역 가능성.
```

### 5단계: 외부 IP 통신 확인

```bash
ping 8.8.8.8
```

판단 기준:

```text
게이트웨이 ping 성공 + 8.8.8.8 실패:
라우팅, NAT, 상위 회선, 방화벽 문제 가능성.

8.8.8.8 성공 + 도메인 실패:
DNS 문제 가능성.
```

### 6단계: DNS 확인

Windows:

```cmd
nslookup google.com
```

Linux:

```bash
nslookup google.com
dig google.com
resolvectl status
```

판단 기준:

```text
IP 통신은 되는데 도메인 조회 실패:
DHCP의 DNS 옵션 문제 또는 DNS 서버 문제 가능성.
```

### 7단계: DHCP 서버 또는 공유기 확인

서버 측에서 확인할 것:

- DHCP 서비스 실행 여부
- IP pool 여유
- scope 설정
- gateway option
- DNS option
- lease 목록
- 서버 로그
- 방화벽
- VLAN별 scope
- DHCP Relay 설정

### 8단계: 네트워크 인프라 확인

확인할 것:

- 스위치 포트 VLAN
- trunk 허용 VLAN
- L3 스위치 SVI 상태
- DHCP Relay
- 라우터 인터페이스 상태
- ACL
- DHCP Snooping
- Rogue DHCP
- 케이블/링크 상태

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
IP가 169.254.x.x:
DHCP 서버로부터 IP를 받지 못했을 가능성이 높다.

IP가 없음:
인터페이스 down, DHCP 클라이언트 미동작, 네트워크 설정 오류 가능성이 있다.

IP는 있음 + 게이트웨이 없음:
DHCP option 3 누락 또는 DHCP 설정 오류 가능성이 있다.

IP는 있음 + DNS 없음:
DHCP option 6 누락 또는 DNS 설정 문제 가능성이 있다.

IP, 게이트웨이, DNS가 모두 있음 + 인터넷 안 됨:
DHCP보다는 gateway, routing, NAT, firewall 문제일 가능성이 높다.

8.8.8.8 ping 성공 + google.com 실패:
DHCP 자체보다는 DNS 설정 또는 DNS 서버 문제일 가능성이 높다.

같은 네트워크의 모든 장비가 IP를 못 받음:
DHCP 서버, 공유기, DHCP relay, 스위치, VLAN 문제 가능성이 높다.

특정 장비만 IP를 못 받음:
클라이언트 설정, NIC, 케이블, Wi-Fi, MAC 차단, OS 문제 가능성이 높다.

특정 VLAN만 IP를 못 받음:
VLAN, DHCP Relay, scope, trunk 문제 가능성이 높다.

예상과 다른 대역의 IP를 받음:
Rogue DHCP, 잘못된 SSID, 잘못된 VM 네트워크 모드, 개인 공유기 연결 가능성이 있다.

DHCP 서버 로그에 Discover가 없음:
클라이언트 요청이 서버까지 도달하지 못하는 네트워크 경로 문제 가능성이 높다.

Discover는 있는데 Offer가 없음:
DHCP 서버 설정, IP pool, scope, 방화벽 문제 가능성이 있다.

Offer는 있는데 ACK가 없음:
클라이언트 수락 실패, 중간 패킷 손실, 보안 장비, 충돌 가능성이 있다.
```

---

## 문제 유형별 해결 방법

### IP가 169.254.x.x일 때

1. 케이블 또는 Wi-Fi 연결 확인
2. 올바른 네트워크에 연결되었는지 확인
3. DHCP 재요청 수행
4. DHCP 서버 또는 공유기 상태 확인
5. 같은 네트워크의 다른 장비가 IP를 받는지 확인
6. DHCP pool 고갈 여부 확인
7. VLAN 또는 DHCP Relay 확인
8. 방화벽 또는 보안 장비 확인

Windows:

```cmd
ipconfig /release
ipconfig /renew
```

Linux:

```bash
sudo dhclient -v <interface>
```

### IP는 받았지만 인터넷이 안 될 때

1. 기본 게이트웨이 확인
2. 게이트웨이 ping 확인
3. 외부 IP ping 확인
4. DNS 확인
5. 라우팅 테이블 확인
6. NAT 또는 상위 라우터 확인
7. 방화벽 확인

명령어:

```bash
ip route
ping <gateway_ip>
ping 8.8.8.8
nslookup google.com
```

### IP는 받았지만 DNS가 안 될 때

1. DHCP로 받은 DNS 서버 확인
2. DNS 서버에 ping 가능한지 확인
3. nslookup 또는 dig 실행
4. 임시로 다른 DNS 설정 후 비교
5. DHCP 서버의 DNS option 확인

Windows:

```cmd
ipconfig /all
nslookup google.com
```

Linux:

```bash
resolvectl status
cat /etc/resolv.conf
dig google.com
```

### 특정 VLAN만 DHCP가 안 될 때

1. 해당 VLAN의 SVI 또는 게이트웨이 확인
2. DHCP Relay 설정 확인
3. DHCP 서버에 해당 VLAN scope가 있는지 확인
4. trunk에 해당 VLAN이 허용되어 있는지 확인
5. DHCP 서버 로그에 Discover가 도착하는지 확인
6. ACL 또는 DHCP Snooping 확인

### VM에서 DHCP가 안 될 때

1. VM 네트워크 모드 확인
2. NAT, Bridge, Host-only 중 의도한 모드인지 확인
3. 가상 NIC connected 상태 확인
4. Bridge 대상 물리 어댑터 확인
5. Host-only DHCP 서버 활성화 여부 확인
6. VM 내부 OS에서 DHCP 설정 확인
7. `ip addr`, `ip route`, `nmcli dev show` 확인

### OpenWrt에서 DHCP가 안 될 때

1. LAN 인터페이스 IP 확인
2. dnsmasq 상태 확인
3. DHCP 설정 확인
4. lease 목록 확인
5. 클라이언트가 LAN에 붙어 있는지 확인
6. WAN/LAN 포트 혼동 여부 확인
7. 로그 확인

명령어:

```sh
ip addr
ip route
uci show dhcp
cat /tmp/dhcp.leases
/etc/init.d/dnsmasq status
logread | grep dnsmasq
```

---

## 에이전트 응답 전략

DHCP 문제로 의심될 때 에이전트는 바로 해결책만 제시하지 말고, 먼저 사용자의 현재 상태를 확인해야 한다.

우선 물어볼 정보:

```text
1. 사용 중인 OS가 Windows인지 Linux인지
2. 유선인지 Wi-Fi인지
3. ipconfig /all 또는 ip addr 결과
4. IP 주소가 169.254.x.x인지
5. 기본 게이트웨이가 있는지
6. 같은 네트워크의 다른 장비는 정상인지
7. 공유기/서버/VM 환경인지
```

에이전트가 우선 요청할 명령어:

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
ip addr
ip route
nmcli dev show
```

VM 또는 서버 환경이면 추가:

```bash
journalctl -u NetworkManager -n 100 --no-pager
```

---

## 에이전트 응답 예시

### 예시 1: 169.254 주소가 잡힌 경우

사용자 입력:

```text
ipconfig 보니까 IPv4가 169.254.30.11로 나와
```

에이전트 응답:

```text
169.254.x.x 주소는 Windows가 DHCP 서버로부터 정상적인 IP를 받지 못했을 때 자동으로 잡는 APIPA 주소입니다. 즉, 현재 장비가 DHCP 서버에서 IP를 받지 못한 상태일 가능성이 높습니다.

먼저 아래 순서로 확인하세요.

1. 같은 공유기나 같은 네트워크에 연결된 다른 장비는 인터넷이 되는지 확인
2. `ipconfig /all`에서 DHCP Server 항목이 있는지 확인
3. `ipconfig /release` 후 `ipconfig /renew` 실행
4. 유선이면 케이블과 포트 변경
5. Wi-Fi면 올바른 SSID에 연결되었는지 확인
6. 회사/학교 VLAN 환경이면 DHCP Relay 또는 VLAN 설정 문제 가능성 확인

만약 다른 장비도 IP를 못 받는다면 DHCP 서버나 공유기 DHCP 기능 문제일 가능성이 높고, 내 PC만 안 된다면 PC의 네트워크 어댑터 또는 설정 문제일 가능성이 큽니다.
```

### 예시 2: IP는 있는데 게이트웨이가 없는 경우

사용자 입력:

```text
IP는 192.168.1.40인데 기본 게이트웨이가 비어있어
```

에이전트 응답:

```text
IP 주소는 받았지만 기본 게이트웨이가 없다면 외부 네트워크나 인터넷으로 나갈 경로가 없는 상태입니다. DHCP 서버가 IP는 배포했지만 Router Option, 즉 기본 게이트웨이 옵션을 제대로 내려주지 않았을 가능성이 있습니다.

확인할 내용은 다음과 같습니다.

1. `ipconfig /all` 또는 `ip route`로 기본 게이트웨이 확인
2. DHCP 서버 설정에서 gateway/router option 확인
3. 같은 네트워크의 다른 장비는 게이트웨이를 정상적으로 받는지 비교
4. 수동 IP 설정이 섞여 있지 않은지 확인

정상이라면 기본 라우트가 `default via 192.168.1.1` 같은 형태로 존재해야 합니다.
```

### 예시 3: IP는 있는데 DNS가 없는 경우

사용자 입력:

```text
인터넷은 되는 것 같은데 사이트 주소가 안 열려
```

에이전트 응답:

```text
IP 통신은 되지만 도메인 주소가 안 열린다면 DNS 문제일 가능성이 있습니다. DHCP 서버가 DNS 서버 정보를 잘못 배포했거나 DNS 서버 자체가 응답하지 않을 수 있습니다.

먼저 다음을 확인하세요.

Windows:
`ipconfig /all`
`nslookup google.com`

Linux:
`resolvectl status`
`cat /etc/resolv.conf`
`dig google.com`

만약 `ping 8.8.8.8`은 되는데 `ping google.com`이 실패한다면 DHCP 자체보다는 DHCP로 받은 DNS 설정 또는 DNS 서버 문제일 가능성이 높습니다.
```

### 예시 4: VM에서 IP가 안 잡히는 경우

사용자 입력:

```text
VirtualBox 로키 리눅스에서 IP가 안 잡혀
```

에이전트 응답:

```text
가상머신에서 IP가 안 잡히는 경우는 DHCP 서버 문제뿐 아니라 VM 네트워크 모드 문제일 수 있습니다.

먼저 VirtualBox의 네트워크 모드가 NAT, Bridge, Host-only 중 무엇인지 확인해야 합니다.

- NAT: VirtualBox 내부 DHCP에서 IP를 받는 것이 일반적입니다.
- Bridge: 실제 공유기나 학교/회사 네트워크의 DHCP 서버에서 IP를 받습니다.
- Host-only: 호스트와 VM 사이의 내부망이며, Host-only DHCP 서버가 꺼져 있으면 IP를 못 받을 수 있습니다.

VM 내부에서는 다음 명령어를 실행하세요.

`ip addr`
`ip route`
`nmcli dev status`
`nmcli dev show`

만약 IP가 없거나 169.254 대역이라면 VM 어댑터가 연결되어 있는지, DHCP가 활성화되어 있는지, 네트워크 모드가 의도한 값인지 확인해야 합니다.
```

---

## 주의할 점

DHCP 문제를 진단할 때 다음을 주의해야 한다.

1. "인터넷이 안 된다"는 말만 듣고 DHCP 문제로 단정하면 안 된다.
2. IP가 정상이어도 게이트웨이 또는 DNS가 잘못되면 인터넷이 안 될 수 있다.
3. 169.254.x.x는 DHCP 실패 가능성이 높지만, 원인이 반드시 DHCP 서버 장애인 것은 아니다.
4. 같은 네트워크의 다른 장비가 정상인지 비교해야 한다.
5. VM 환경에서는 실제 네트워크와 가상 네트워크를 구분해야 한다.
6. 회사/학교 환경에서는 VLAN과 DHCP Relay를 반드시 고려해야 한다.
7. 잘못된 DHCP 서버가 존재하면 IP는 받지만 네트워크가 비정상 동작할 수 있다.
8. DHCP 문제처럼 보여도 실제 원인은 DNS, Gateway, Routing, Firewall일 수 있다.
9. 서버 로그에 Discover가 보이는지 여부는 매우 중요한 판단 기준이다.
10. 운영망에서는 임의로 DHCP 서버를 켜면 네트워크 전체 장애를 유발할 수 있다.

---

## 빠른 진단 요약

```text
1. ipconfig /all 또는 ip addr로 현재 IP 확인
2. 169.254.x.x인지 확인
3. 기본 게이트웨이 존재 여부 확인
4. DNS 서버 존재 여부 확인
5. DHCP 서버 주소 확인
6. 같은 네트워크의 다른 장비 정상 여부 확인
7. 게이트웨이 ping 확인
8. 8.8.8.8 ping 확인
9. google.com DNS 확인
10. DHCP 서버, pool, relay, VLAN, firewall 확인
```

---

## 핵심 키워드

DHCP, DHCP Troubleshooting, IP 자동 할당 실패, IP를 못 받아옴, 169.254, APIPA, DHCP Discover, DHCP Offer, DHCP Request, DHCP ACK, DORA, UDP 67, UDP 68, DHCP Relay, ip helper-address, DHCP Scope, DHCP Pool, Lease, Gateway Option, Router Option, DNS Option, Rogue DHCP, DHCP Snooping, VLAN DHCP 문제, VirtualBox DHCP, VMware DHCP, NAT DHCP, Bridge DHCP, Host-only DHCP, OpenWrt DHCP, dnsmasq, Kea DHCP, NetworkManager DHCP, ipconfig /all, ip addr, ip route, nmcli dev show, dhclient -v, journalctl NetworkManager.