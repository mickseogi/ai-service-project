# DNS Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 DNS 관련 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

DNS 문제는 사용자가 "인터넷이 안 된다", "웹사이트가 안 열린다", "서버를 찾을 수 없다고 뜬다", "IP로는 되는데 주소로는 안 된다"처럼 표현하는 경우가 많다. DNS는 도메인 이름을 IP 주소로 변환하는 역할을 하므로, IP 주소를 직접 사용한 통신은 가능하지만 도메인 이름을 사용한 접속이 실패한다면 DNS 문제를 의심할 수 있다.

에이전트는 사용자의 증상을 듣고 먼저 다음을 구분해야 한다.

- 네트워크 연결 자체가 안 되는 문제인지
- IP 통신은 되지만 도메인 이름 해석만 실패하는 문제인지
- 모든 도메인이 안 되는지
- 특정 도메인만 안 되는지
- DNS 서버 주소가 잘못 설정된 문제인지
- DNS 서버가 응답하지 않는 문제인지
- 로컬 DNS 캐시 문제인지
- 공유기 또는 사내 DNS 캐시 문제인지
- 방화벽이 DNS 요청을 차단하는 문제인지
- DNS 문제가 아니라 Gateway, Routing, Firewall, Proxy, TLS/HTTPS 문제인지

DNS 문제를 정확히 판단하려면 `IP 주소`, `기본 게이트웨이`, `DNS 서버 주소`, `도메인 조회 결과`, `외부 IP ping 결과`, `특정 DNS 서버 지정 조회 결과`, `브라우저 오류 메시지`를 함께 확인해야 한다.

---

## 관련 사용자 표현

사용자는 DNS라는 용어를 직접 말하지 않을 수도 있다. 다음과 같은 표현은 DNS 문제와 관련될 가능성이 있다.

- 인터넷이 안 돼
- 웹사이트가 안 열려
- 주소를 입력하면 서버를 찾을 수 없다고 떠
- IP로는 접속되는데 도메인으로는 안 돼
- `ping 8.8.8.8`은 되는데 `ping google.com`은 안 돼
- 구글 주소가 안 열려
- 특정 사이트만 접속이 안 돼
- 회사 내부 사이트가 안 열려
- 도메인 이름을 해석할 수 없다고 나와
- DNS probe finished라고 떠
- DNS_PROBE_FINISHED_NXDOMAIN 오류가 나와
- DNS_PROBE_FINISHED_NO_INTERNET 오류가 나와
- 서버 DNS 주소를 찾을 수 없다고 나와
- nslookup이 실패해
- resolv.conf가 이상한 것 같아
- DNS 서버가 응답하지 않는다고 나와
- 공유기 바꾼 뒤 사이트 접속이 안 돼
- VPN 연결 후 DNS가 이상해졌어
- 사내망에서는 되는데 집에서는 안 돼
- 집에서는 되는데 학교/회사에서는 안 돼
- 내부 도메인이 안 풀려
- 도메인만 안 되고 IP는 돼
- 8.8.8.8은 ping 되는데 웹사이트가 안 열려
- 리눅스에서 `/etc/resolv.conf`를 봤는데 이상해
- `systemd-resolve --status`나 `resolvectl status` 결과를 모르겠어
- DNS 캐시를 지워야 하나?
- 브라우저에서 서버를 찾을 수 없다고 나와
- Wi-Fi는 연결됐는데 사이트 주소가 안 열려

---

## 핵심 개념

DNS는 Domain Name System의 약자이며, 사람이 읽기 쉬운 도메인 이름을 실제 통신에 필요한 IP 주소로 변환하는 시스템이다.

예를 들어 사용자가 브라우저에 다음 주소를 입력한다고 가정한다.

```text
google.com
```

컴퓨터는 실제로 `google.com`이라는 문자열 자체로 통신하지 않는다. 먼저 DNS 조회를 통해 해당 도메인에 대응하는 IP 주소를 얻고, 그 IP 주소로 TCP/UDP 연결을 시도한다.

즉, 웹사이트 접속 과정은 대략 다음 흐름을 가진다.

```text
사용자 입력: google.com
        ↓
DNS 조회: google.com의 IP 주소 요청
        ↓
DNS 응답: 142.250.x.x 같은 IP 주소 반환
        ↓
반환된 IP 주소로 실제 네트워크 연결 시도
        ↓
HTTP 또는 HTTPS 통신
```

따라서 DNS가 실패하면 실제 인터넷 회선이 살아 있어도 사용자는 웹사이트가 안 열린다고 느낄 수 있다.

---

## DNS 문제와 일반 네트워크 문제의 차이

DNS 문제를 구분하는 가장 기본적인 기준은 다음이다.

```text
IP 주소로 통신 가능 + 도메인 이름으로 통신 실패 = DNS 문제 가능성 높음
IP 주소로도 통신 실패 + 도메인 이름도 실패 = DNS 외의 네트워크 문제 가능성 높음
```

대표적인 확인 방식은 다음과 같다.

```bash
ping 8.8.8.8
ping google.com
```

판단 기준:

```text
ping 8.8.8.8 성공 + ping google.com 실패:
DNS 문제 가능성이 높다.

ping 8.8.8.8 실패 + ping google.com 실패:
DNS 문제 이전에 게이트웨이, 라우팅, 방화벽, 인터넷 연결 문제일 수 있다.

ping 8.8.8.8 성공 + nslookup google.com 실패:
DNS 서버 설정 또는 DNS 서버 응답 문제 가능성이 높다.

nslookup google.com 성공 + 브라우저 접속 실패:
DNS보다는 HTTP/HTTPS, 프록시, 인증서, 방화벽, 웹 서버 문제일 수 있다.
```

주의할 점은 `ping`이 막혀 있는 네트워크도 있다는 것이다. 일부 서버나 방화벽은 ICMP를 차단할 수 있으므로, ping 실패만으로 DNS 문제를 단정하면 안 된다. DNS 진단에는 `nslookup`, `dig`, `resolvectl`, `cat /etc/resolv.conf` 등의 명령어를 함께 사용해야 한다.

---

## DNS 정상 동작 흐름

사용자가 도메인에 접속할 때 DNS 조회는 보통 다음 순서로 진행된다.

### 1. 로컬 캐시 확인

운영체제나 브라우저는 이전에 조회한 DNS 결과를 캐시에 저장할 수 있다.

예를 들어 `google.com`을 이미 조회한 적이 있다면, OS나 브라우저는 DNS 서버에 다시 묻지 않고 캐시된 IP를 사용할 수 있다.

장점:

- 빠른 접속
- DNS 서버 부하 감소

문제 가능성:

- 캐시가 오래됨
- 잘못된 DNS 결과가 캐시에 남음
- 도메인 변경 후 이전 IP로 접속 시도

---

### 2. hosts 파일 확인

운영체제는 DNS 서버에 질의하기 전에 로컬 hosts 파일을 먼저 확인하는 경우가 많다.

Windows hosts 파일 경로:

```text
C:\Windows\System32\drivers\etc\hosts
```

Linux hosts 파일 경로:

```text
/etc/hosts
```

예시:

```text
127.0.0.1 example.com
192.168.10.10 internal.example.local
```

hosts 파일에 잘못된 매핑이 있으면 DNS 서버가 정상이어도 특정 도메인이 잘못된 IP로 연결될 수 있다.

---

### 3. 설정된 DNS 서버로 질의

로컬 캐시와 hosts 파일에 결과가 없으면, 클라이언트는 네트워크 설정에 등록된 DNS 서버로 질의한다.

DNS 서버는 보통 다음 방식으로 설정된다.

- DHCP를 통해 자동으로 받음
- 사용자가 수동으로 설정
- 공유기에서 제공
- 회사 내부 DNS 서버 사용
- VPN 클라이언트가 DNS 서버를 변경
- systemd-resolved 또는 NetworkManager가 관리
- 클라우드/컨테이너 환경의 내부 DNS 사용

---

### 4. 재귀적 조회

일반 클라이언트는 보통 recursive DNS resolver에게 질의한다. 이 resolver는 필요하면 root DNS, TLD DNS, authoritative DNS를 거쳐 최종 IP 주소를 알아낸다.

간단한 흐름:

```text
Client
  ↓
Recursive DNS Resolver
  ↓
Root DNS
  ↓
TLD DNS
  ↓
Authoritative DNS
  ↓
IP 주소 응답
```

사용자가 직접 root DNS나 authoritative DNS를 조회하는 경우는 드물며, 대부분은 ISP DNS, 공유기 DNS, 사내 DNS, Google DNS, Cloudflare DNS 같은 resolver를 사용한다.

---

## DNS에서 사용하는 포트

일반적인 DNS 질의는 UDP 53번 포트를 사용한다.

```text
DNS: UDP 53
```

다만 응답 크기가 크거나 zone transfer 같은 특수한 경우 TCP 53번을 사용할 수 있다.

```text
DNS: TCP 53
```

또한 최근 환경에서는 다음 방식도 사용될 수 있다.

```text
DNS over HTTPS: TCP 443
DNS over TLS: TCP 853
mDNS: UDP 5353
LLMNR: UDP 5355
```

트러블슈팅 에이전트는 일반적인 DNS 문제에서는 우선 UDP/TCP 53번을 확인해야 한다.

방화벽이나 보안 장비가 UDP 53을 차단하면 DNS 질의가 실패할 수 있다. 단, 웹브라우저가 DoH를 사용 중이면 OS DNS 설정과 브라우저 DNS 동작이 다를 수 있다.

---

## DNS 레코드 기본 개념

DNS 문제를 더 정확히 진단하려면 주요 레코드 유형을 알아야 한다.

### A 레코드

도메인 이름을 IPv4 주소로 변환한다.

```text
example.com -> 93.184.216.34
```

### AAAA 레코드

도메인 이름을 IPv6 주소로 변환한다.

```text
example.com -> 2606:2800:220:1:248:1893:25c8:1946
```

### CNAME 레코드

도메인을 다른 도메인의 별칭으로 연결한다.

```text
www.example.com -> example.com
```

### MX 레코드

메일 서버 정보를 나타낸다.

```text
example.com mail is handled by mail.example.com
```

### TXT 레코드

텍스트 정보를 저장한다. SPF, DKIM, 도메인 인증 등에 사용된다.

### NS 레코드

해당 도메인의 authoritative name server를 나타낸다.

### PTR 레코드

IP 주소를 도메인 이름으로 역방향 조회할 때 사용한다.

---

## DNS 문제의 대표 증상

### 1. `ping 8.8.8.8`은 되지만 `ping google.com`은 안 됨

가장 전형적인 DNS 문제 증상이다.

가능한 원인:

- DNS 서버 주소가 잘못 설정됨
- DNS 서버가 응답하지 않음
- DHCP에서 DNS 정보를 받지 못함
- `/etc/resolv.conf`가 잘못됨
- systemd-resolved 설정 문제
- NetworkManager DNS 설정 문제
- 방화벽이 UDP 53을 차단
- 사내 DNS 장애
- 공유기 DNS 프록시 장애
- VPN DNS 설정 꼬임

판단:

```text
외부 IP 통신은 가능하므로 기본 게이트웨이와 라우팅은 어느 정도 동작한다.
도메인 이름 해석만 실패하므로 DNS 설정 또는 DNS 서버 문제 가능성이 높다.
```

---

### 2. 웹사이트 주소를 입력하면 서버를 찾을 수 없다고 뜸

브라우저에서 다음과 같은 오류가 나타날 수 있다.

```text
DNS_PROBE_FINISHED_NXDOMAIN
DNS_PROBE_FINISHED_NO_INTERNET
DNS_PROBE_FINISHED_BAD_CONFIG
Server DNS address could not be found
This site can't be reached
서버 IP 주소를 찾을 수 없습니다
```

가능한 원인:

- DNS 조회 실패
- 잘못된 DNS 서버 사용
- 도메인이 실제로 존재하지 않음
- hosts 파일이 잘못됨
- 브라우저 DNS 캐시 문제
- VPN 또는 프록시 문제
- 보안 프로그램이 DNS를 가로챔
- 회사/학교 네트워크의 DNS 정책 차단

주의:

브라우저 오류 메시지만으로 DNS 문제를 확정하면 안 된다. 반드시 `nslookup` 또는 `dig`로 도메인 조회를 직접 확인해야 한다.

---

### 3. 특정 도메인만 접속되지 않음

모든 사이트가 안 되는 것이 아니라 특정 도메인만 안 된다면 원인을 다르게 봐야 한다.

가능한 원인:

- 해당 도메인의 DNS 레코드 문제
- 도메인 만료
- authoritative DNS 장애
- 특정 DNS 서버의 캐시 문제
- 내부 DNS split-horizon 문제
- 사내 DNS에만 등록된 내부 도메인
- hosts 파일에 잘못된 항목 존재
- 보안 장비 또는 DNS 필터링
- CDN 장애
- IPv6 AAAA 레코드 문제
- DNSSEC 검증 실패

진단 방법:

```bash
nslookup target-domain.com
nslookup target-domain.com 8.8.8.8
nslookup target-domain.com 1.1.1.1
dig target-domain.com
dig target-domain.com @8.8.8.8
dig target-domain.com @1.1.1.1
```

판단 기준:

```text
기본 DNS에서는 실패하지만 8.8.8.8에서는 성공:
현재 DNS 서버 문제 가능성.

8.8.8.8과 1.1.1.1에서도 모두 실패:
도메인 자체 문제, authoritative DNS 문제, 도메인 오타 가능성.

사내망에서는 성공하고 외부망에서는 실패:
내부 DNS 전용 도메인일 수 있음.

외부망에서는 성공하고 사내망에서는 실패:
사내 DNS, 보안 장비, 프록시, DNS 필터링 문제 가능성.
```

---

### 4. 내부 도메인만 접속되지 않음

회사, 학교, 연구실, 사내망에서는 내부 전용 도메인을 사용하는 경우가 있다.

예시:

```text
intranet.company.local
gitlab.internal
nas.local
server.office.lan
```

이런 도메인은 외부 DNS 서버에서는 조회되지 않을 수 있다.

가능한 원인:

- 사내 DNS 서버를 사용하지 않음
- VPN 연결이 끊김
- VPN DNS push가 실패함
- search domain 설정 누락
- split DNS 설정 문제
- 내부 DNS 서버 장애
- DHCP에서 내부 DNS 서버를 받지 못함

진단:

```bash
nslookup intranet.company.local
nslookup intranet.company.local <internal_dns_ip>
resolvectl status
cat /etc/resolv.conf
ipconfig /all
```

판단:

```text
내부 DNS 서버를 직접 지정하면 성공:
클라이언트 DNS 설정 문제 가능성.

내부 DNS 서버를 직접 지정해도 실패:
내부 DNS 서버 또는 레코드 문제 가능성.

VPN 연결 시만 성공:
해당 도메인은 내부망/VPN 전용일 가능성.
```

---

### 5. DNS가 느림

도메인 조회가 아예 실패하지는 않지만 웹사이트 접속이 매우 느릴 수 있다.

가능한 원인:

- DNS 서버 응답 지연
- 1차 DNS 서버가 죽고 2차 DNS 서버로 timeout 후 전환
- IPv6 DNS 조회 지연
- 잘못된 DNS 서버가 우선순위에 있음
- VPN DNS 서버가 느림
- 공유기 DNS 프록시 성능 문제
- 보안 DNS 필터링 지연
- 네트워크 패킷 손실

진단:

```bash
time nslookup google.com
dig google.com
dig google.com @8.8.8.8
dig google.com @1.1.1.1
```

Linux에서 `dig` 결과의 Query time을 확인한다.

```text
Query time: 20 msec
```

판단:

```text
기본 DNS만 느림:
현재 DNS 서버 문제 가능성.

모든 DNS가 느림:
네트워크 지연, 방화벽, 회선 문제 가능성.

처음 조회만 느리고 이후 빠름:
DNS 캐시 동작일 수 있음.
```

---

### 6. VPN 연결 후 DNS가 이상해짐

VPN은 클라이언트의 DNS 서버, 라우팅 테이블, search domain을 변경할 수 있다.

가능한 증상:

- VPN 연결 후 일반 웹사이트가 안 열림
- VPN 연결 후 사내 도메인만 열림
- VPN 연결 후 사내 도메인이 안 열림
- VPN 해제 후에도 DNS가 이상함
- 특정 인터페이스의 DNS가 우선 적용됨
- split tunneling 설정 문제

확인:

Windows:

```cmd
ipconfig /all
nslookup internal-domain
route print
```

Linux:

```bash
resolvectl status
ip route
nmcli dev show
```

판단:

```text
VPN 인터페이스의 DNS가 우선순위를 가짐:
VPN 정책에 따라 정상일 수도 있고 설정 오류일 수도 있다.

VPN 연결 시 내부 도메인 실패:
VPN DNS push, split DNS, search domain 문제 가능성.

VPN 해제 후 DNS 실패:
DNS 설정이 원복되지 않았거나 캐시가 꼬였을 수 있다.
```

---

### 7. IPv4는 되는데 IPv6 때문에 접속이 지연되거나 실패함

일부 환경에서는 도메인의 AAAA 레코드가 먼저 조회되고, 클라이언트가 IPv6 연결을 시도하다가 실패하면서 접속이 느려질 수 있다.

가능한 원인:

- IPv6 주소는 받았지만 IPv6 라우팅이 불완전함
- DNS에서 AAAA 레코드는 받지만 실제 IPv6 통신이 안 됨
- 방화벽이 IPv6를 차단
- 네트워크에서 IPv6 설정이 부분적으로만 활성화됨

진단:

```bash
nslookup google.com
dig A google.com
dig AAAA google.com
ping 8.8.8.8
ping6 2001:4860:4860::8888
```

판단:

```text
A 레코드 통신은 정상 + AAAA 레코드 통신 실패:
IPv6 설정 문제 가능성.

IPv6를 끄면 정상 접속:
IPv6 라우팅 또는 DNS 우선순위 문제 가능성.
```

---

## Possible Causes

DNS 문제의 원인은 크게 클라이언트 설정 문제, DNS 서버 문제, 네트워크 경로 문제, 캐시 문제, 보안 정책 문제, 내부망/VPN 문제로 나눌 수 있다.

---

### 1. DNS 서버 주소가 잘못 설정되어 있음

DNS 서버 주소가 잘못되면 도메인 이름 해석이 실패한다.

예시:

```text
DNS Server: 192.168.1.1
```

공유기 DNS 프록시가 정상이라면 이 값은 문제 없을 수 있다. 하지만 공유기의 DNS 기능이 죽었거나, 실제 DNS 서버가 아닌 주소가 설정되어 있다면 DNS 조회가 실패한다.

잘못된 예:

```text
DNS Server: 192.168.99.99
DNS Server: 0.0.0.0
DNS Server: 존재하지 않는 내부 서버 IP
```

확인 명령어:

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
cat /etc/resolv.conf
resolvectl status
nmcli dev show
```

해결:

- DHCP로 DNS를 다시 받기
- 수동 DNS를 올바른 주소로 변경
- 공유기 DNS 프록시 재시작
- 사내망이라면 내부 DNS 주소 확인
- VPN 환경이라면 VPN DNS 설정 확인

---

### 2. DNS 서버가 응답하지 않음

DNS 서버 주소가 맞더라도 해당 서버가 응답하지 않으면 DNS 조회가 실패한다.

가능한 원인:

- DNS 서버 장애
- DNS 서비스 중지
- DNS 서버 방화벽 문제
- 네트워크 경로 문제
- DNS 서버 과부하
- 공유기 DNS 프록시 장애
- 사내 DNS 장애

확인:

```bash
nslookup google.com <dns_server_ip>
dig google.com @<dns_server_ip>
```

예시:

```bash
nslookup google.com 8.8.8.8
dig google.com @8.8.8.8
```

DNS 서버 포트 확인:

```bash
nc -vz <dns_server_ip> 53
```

UDP DNS는 `nc`만으로 완벽히 판단하기 어렵지만, TCP 53 접근 가능 여부를 참고할 수 있다.

Linux에서 DNS 패킷 확인:

```bash
sudo tcpdump -i <interface> -n port 53
```

판단:

```text
DNS 요청은 나가는데 응답이 없음:
DNS 서버 장애, 방화벽, 라우팅 문제 가능성.

다른 DNS 서버를 지정하면 성공:
기존 DNS 서버 문제 가능성.

어떤 DNS 서버도 응답하지 않음:
클라이언트 네트워크, 방화벽, UDP 53 차단 가능성.
```

---

### 3. `/etc/resolv.conf` 설정 문제

Linux에서는 `/etc/resolv.conf`가 DNS 서버 정보를 담는 파일로 자주 사용된다.

일반적인 예:

```text
nameserver 8.8.8.8
nameserver 1.1.1.1
```

systemd-resolved 사용 환경에서는 다음처럼 보일 수 있다.

```text
nameserver 127.0.0.53
options edns0 trust-ad
search localdomain
```

여기서 `127.0.0.53`은 외부 DNS 서버가 아니라 로컬 stub resolver이다. 이 경우 실제 DNS 서버는 `resolvectl status`로 확인해야 한다.

확인:

```bash
cat /etc/resolv.conf
resolvectl status
```

주의:

- `/etc/resolv.conf`를 직접 수정해도 NetworkManager나 systemd-resolved가 다시 덮어쓸 수 있다.
- `127.0.0.53` 자체가 항상 문제인 것은 아니다.
- 실제 upstream DNS 서버를 확인해야 한다.
- 컨테이너 환경에서는 `/etc/resolv.conf`가 호스트 또는 Docker 네트워크에 의해 자동 생성될 수 있다.

---

### 4. systemd-resolved 문제

현대 Linux 배포판에서는 systemd-resolved가 DNS를 관리하는 경우가 많다.

확인 명령어:

```bash
resolvectl status
```

구버전 명령어:

```bash
systemd-resolve --status
```

서비스 상태 확인:

```bash
systemctl status systemd-resolved
```

재시작:

```bash
sudo systemctl restart systemd-resolved
```

캐시 초기화:

```bash
sudo resolvectl flush-caches
```

또는:

```bash
sudo systemd-resolve --flush-caches
```

확인할 항목:

```text
Global DNS Servers
Link별 DNS Servers
Current DNS Server
DNSSEC 설정
DNS Domain
DefaultRoute 여부
```

판단 기준:

```text
resolv.conf에는 127.0.0.53만 보이지만 resolvectl status에 정상 DNS 서버가 있음:
systemd-resolved를 통한 정상 구성일 수 있음.

resolvectl status에 DNS 서버가 없음:
DHCP 또는 NetworkManager DNS 설정 문제 가능성.

특정 인터페이스에만 DNS가 설정됨:
VPN, Wi-Fi, Ethernet 우선순위 문제 가능성.
```

---

### 5. NetworkManager DNS 설정 문제

Linux 데스크톱이나 Rocky, Fedora, Ubuntu 일부 환경에서는 NetworkManager가 DNS 정보를 관리한다.

확인:

```bash
nmcli dev show
```

확인할 항목:

```text
IP4.DNS
IP4.DOMAIN
IP4.GATEWAY
IP4.DHCP_SERVER
```

특정 연결 확인:

```bash
nmcli con show "<connection-name>"
```

수동 DNS 설정 예시:

```bash
sudo nmcli con mod "<connection-name>" ipv4.dns "8.8.8.8 1.1.1.1"
sudo nmcli con mod "<connection-name>" ipv4.ignore-auto-dns yes
sudo nmcli con up "<connection-name>"
```

DHCP로 받은 DNS를 사용하려면:

```bash
sudo nmcli con mod "<connection-name>" ipv4.ignore-auto-dns no
sudo nmcli con mod "<connection-name>" ipv4.method auto
sudo nmcli con up "<connection-name>"
```

주의:

- `ipv4.ignore-auto-dns yes`가 설정되어 있으면 DHCP에서 받은 DNS를 무시한다.
- 수동 DNS가 잘못되어 있으면 DHCP가 정상이어도 DNS 장애처럼 보인다.
- VPN 연결이 DNS 우선순위를 변경할 수 있다.

---

### 6. DHCP에서 DNS 옵션을 받지 못함

DNS 서버 주소는 DHCP를 통해 자동으로 배포되는 경우가 많다.

DHCP에서 DNS 서버 정보를 내려주지 않으면 클라이언트는 IP 주소는 받아도 도메인 이름을 해석하지 못할 수 있다.

DHCP DNS 옵션:

```text
Option 6: DNS Server
```

증상:

```text
IP 주소 있음
기본 게이트웨이 있음
8.8.8.8 ping 성공
DNS 서버 주소 없음
도메인 조회 실패
```

확인:

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
nmcli dev show
cat /etc/resolv.conf
resolvectl status
```

해결:

- DHCP 서버 설정에서 DNS option 확인
- 공유기 DHCP 설정에서 DNS 서버 항목 확인
- 사내 DHCP scope의 DNS 옵션 확인
- 임시로 수동 DNS 설정 후 비교

---

### 7. 사내 DNS 또는 공유기 DNS 캐시 문제

가정용 공유기나 사내 DNS 서버는 클라이언트의 DNS 요청을 받아 상위 DNS로 전달하는 DNS 프록시 또는 캐시 역할을 할 수 있다.

예시:

```text
Client DNS Server: 192.168.0.1
```

이 경우 클라이언트는 공유기에게 DNS 질의를 보내고, 공유기는 ISP DNS나 외부 DNS로 질의를 전달한다.

가능한 문제:

- 공유기 DNS 프록시가 멈춤
- 공유기 캐시에 잘못된 결과가 남음
- 사내 DNS 캐시가 오래됨
- 상위 DNS로 전달이 안 됨
- 특정 도메인만 잘못 캐싱됨
- 공유기 재부팅 후 해결됨

진단:

```bash
nslookup google.com 192.168.0.1
nslookup google.com 8.8.8.8
nslookup google.com 1.1.1.1
```

판단:

```text
공유기 DNS에서는 실패하지만 8.8.8.8에서는 성공:
공유기 DNS 프록시 또는 ISP DNS 문제 가능성.

사내 DNS에서는 실패하지만 외부 DNS에서는 성공:
사내 DNS 캐시, 정책, 포워딩 문제 가능성.

사내 내부 도메인은 사내 DNS에서만 성공:
내부 도메인 구조상 정상일 수 있음.
```

---

### 8. DNS 캐시 문제

DNS 결과는 OS, 브라우저, 공유기, 사내 DNS 서버 등에 캐시될 수 있다.

캐시 문제는 다음 상황에서 발생할 수 있다.

- 도메인의 IP가 변경됨
- 서버 이전 후 이전 IP로 계속 접속됨
- DNS 레코드 수정 후 반영이 늦음
- 잘못된 NXDOMAIN 결과가 캐시됨
- 브라우저 자체 DNS 캐시가 남음

Windows DNS 캐시 초기화:

```cmd
ipconfig /flushdns
```

Linux systemd-resolved 캐시 초기화:

```bash
sudo resolvectl flush-caches
```

구버전:

```bash
sudo systemd-resolve --flush-caches
```

브라우저 캐시:

- Chrome: `chrome://net-internals/#dns`
- 브라우저 재시작
- 시크릿 모드 테스트
- 다른 브라우저 테스트

주의:

DNS 캐시를 지워도 authoritative DNS나 상위 DNS 캐시에 남아 있는 정보는 즉시 바뀌지 않을 수 있다. TTL이 남아 있으면 일부 DNS 서버는 기존 결과를 계속 반환할 수 있다.

---

### 9. 방화벽이 DNS 요청을 차단

DNS는 일반적으로 UDP 53을 사용한다. 방화벽이나 보안 장비가 UDP 53을 차단하면 DNS 조회가 실패한다.

가능한 차단 위치:

- 클라이언트 OS 방화벽
- Linux firewalld/ufw/iptables/nftables
- Windows Defender Firewall
- 공유기 보안 설정
- 회사/학교 방화벽
- 클라우드 보안 그룹
- 가상머신 NAT/Bridge 네트워크
- 컨테이너 네트워크 정책
- 보안 프로그램 또는 백신

Linux에서 DNS 패킷 확인:

```bash
sudo tcpdump -i <interface> -n port 53
```

firewalld 확인:

```bash
sudo firewall-cmd --list-all
```

ufw 확인:

```bash
sudo ufw status verbose
```

iptables 확인:

```bash
sudo iptables -L -n -v
```

nftables 확인:

```bash
sudo nft list ruleset
```

판단:

```text
DNS 요청 패킷이 나가지 않음:
클라이언트 로컬 방화벽 또는 DNS 설정 문제 가능성.

DNS 요청은 나가지만 응답이 없음:
중간 방화벽, DNS 서버 방화벽, 라우팅 문제 가능성.

특정 DNS 서버만 차단됨:
네트워크 정책 또는 보안 장비 정책 가능성.
```

---

### 10. hosts 파일 문제

hosts 파일에 잘못된 내용이 있으면 특정 도메인이 DNS 서버 조회 없이 잘못된 IP로 연결될 수 있다.

Windows:

```text
C:\Windows\System32\drivers\etc\hosts
```

Linux:

```text
/etc/hosts
```

예시 문제:

```text
127.0.0.1 google.com
192.168.1.100 example.com
```

증상:

- 특정 도메인만 이상한 곳으로 연결됨
- nslookup 결과는 정상인데 브라우저 접속은 이상함
- ping 결과가 예상과 다른 IP로 향함

주의:

`nslookup`은 보통 DNS 서버에 직접 질의하므로 hosts 파일 영향을 받지 않을 수 있다. 반면 브라우저나 `ping`은 OS 이름 해석 순서에 따라 hosts 파일 영향을 받을 수 있다.

Linux 이름 해석 순서는 `/etc/nsswitch.conf`에서 확인할 수 있다.

```bash
cat /etc/nsswitch.conf
```

확인할 항목:

```text
hosts: files dns
```

이 설정은 hosts 파일을 먼저 보고, 그 다음 DNS를 조회한다는 의미이다.

---

### 11. 도메인 자체 문제

특정 도메인만 조회되지 않는 경우, 클라이언트 문제가 아니라 도메인 자체 문제일 수 있다.

가능한 원인:

- 도메인 만료
- DNS 레코드 삭제
- authoritative DNS 장애
- 잘못된 NS 설정
- DNSSEC 오류
- CDN DNS 문제
- 도메인 오타
- 등록되지 않은 도메인

진단:

```bash
dig domain.com
dig NS domain.com
dig A domain.com
dig AAAA domain.com
dig +trace domain.com
```

판단:

```text
모든 DNS 서버에서 NXDOMAIN:
도메인이 존재하지 않거나 오타일 가능성.

특정 DNS 서버에서만 NXDOMAIN:
캐시 문제 또는 DNS 서버 정책 문제 가능성.

NS 조회 실패:
도메인의 authoritative DNS 설정 문제 가능성.
```

---

### 12. DNSSEC 문제

DNSSEC은 DNS 응답의 무결성을 검증하기 위한 보안 기능이다.

DNSSEC 설정이 잘못되면 일부 DNS 서버에서 해당 도메인 조회가 실패할 수 있다.

증상:

- 특정 도메인만 일부 DNS 서버에서 실패
- DNSSEC 검증을 하는 resolver에서만 실패
- 다른 DNS 서버에서는 조회 가능
- `SERVFAIL`이 발생

진단:

```bash
dig domain.com
dig domain.com +dnssec
dig domain.com @8.8.8.8
dig domain.com @1.1.1.1
```

판단:

```text
응답 코드가 SERVFAIL:
DNSSEC, authoritative DNS, resolver 문제 가능성.

DNSSEC 검증 resolver에서만 실패:
도메인의 DNSSEC 설정 문제 가능성.
```

---

### 13. 프록시 또는 보안 프로그램 문제

일부 회사/학교 환경에서는 프록시, 보안 에이전트, 백신, 웹 필터링 프로그램이 DNS나 웹 접속에 영향을 줄 수 있다.

증상:

- nslookup은 성공하지만 브라우저 접속 실패
- 특정 카테고리 사이트만 차단
- 회사망에서만 접속 실패
- 보안 프로그램 설치 후 DNS 이상
- VPN 또는 프록시 사용 시만 문제 발생

판단:

```text
DNS 조회 성공 + IP 연결 성공 + 브라우저만 실패:
DNS보다는 프록시, TLS, 인증서, 방화벽, 웹 필터링 문제 가능성.

다른 브라우저에서는 정상:
브라우저 설정 또는 캐시 문제 가능성.

시크릿 모드에서는 정상:
브라우저 확장 프로그램 또는 캐시 문제 가능성.
```

---

## Recommended Commands

DNS 문제는 운영체제별로 확인 명령어가 다르다.

---

## Windows 클라이언트 진단 명령어

### 전체 네트워크 설정 확인

```cmd
ipconfig /all
```

확인할 항목:

```text
IPv4 Address
Default Gateway
DNS Servers
DHCP Enabled
DHCP Server
Connection-specific DNS Suffix
```

판단 기준:

```text
DNS Servers가 없음:
DHCP DNS 옵션 누락 또는 수동 설정 문제 가능성.

DNS Servers가 예상과 다름:
잘못된 DHCP, Rogue DHCP, VPN, 수동 설정 문제 가능성.

Default Gateway가 없음:
DNS 이전에 외부 네트워크 연결 문제 가능성.

IPv4가 169.254.x.x:
DNS 문제가 아니라 DHCP 실패 가능성이 높음.
```

### 외부 IP 통신 확인

```cmd
ping 8.8.8.8
```

### 도메인 통신 확인

```cmd
ping google.com
```

### DNS 조회 확인

```cmd
nslookup google.com
```

### 특정 DNS 서버를 지정하여 조회

```cmd
nslookup google.com 8.8.8.8
nslookup google.com 1.1.1.1
```

### DNS 캐시 초기화

```cmd
ipconfig /flushdns
```

### 라우팅 테이블 확인

```cmd
route print
```

### hosts 파일 확인

관리자 권한으로 다음 파일 확인:

```text
C:\Windows\System32\drivers\etc\hosts
```

---

## Linux 클라이언트 진단 명령어

### IP 주소 확인

```bash
ip addr
```

### 라우팅 확인

```bash
ip route
```

### DNS 설정 파일 확인

```bash
cat /etc/resolv.conf
```

### systemd-resolved 상태 확인

```bash
resolvectl status
```

구버전:

```bash
systemd-resolve --status
```

### DNS 조회

```bash
nslookup google.com
```

### dig 사용

```bash
dig google.com
```

### 특정 DNS 서버 지정

```bash
dig google.com @8.8.8.8
dig google.com @1.1.1.1
nslookup google.com 8.8.8.8
```

### A 레코드만 조회

```bash
dig A google.com
```

### AAAA 레코드 조회

```bash
dig AAAA google.com
```

### DNS 응답 경로 추적

```bash
dig +trace google.com
```

### NetworkManager DNS 확인

```bash
nmcli dev show
```

확인할 항목:

```text
IP4.DNS
IP4.DOMAIN
IP4.GATEWAY
IP4.DHCP_SERVER
```

### DNS 캐시 초기화

```bash
sudo resolvectl flush-caches
```

구버전:

```bash
sudo systemd-resolve --flush-caches
```

### systemd-resolved 재시작

```bash
sudo systemctl restart systemd-resolved
```

### NetworkManager 재시작

```bash
sudo systemctl restart NetworkManager
```

### DNS 패킷 캡처

```bash
sudo tcpdump -i <interface> -n port 53
```

예시:

```bash
sudo tcpdump -i eth0 -n port 53
sudo tcpdump -i ens33 -n port 53
sudo tcpdump -i enp0s3 -n port 53
```

---

## OpenWrt DNS 진단 명령어

OpenWrt에서는 보통 `dnsmasq`가 DHCP와 DNS forwarding 역할을 함께 수행한다.

### DNS/DHCP 서비스 상태 확인

```sh
/etc/init.d/dnsmasq status
```

### dnsmasq 재시작

```sh
/etc/init.d/dnsmasq restart
```

### DNS 관련 설정 확인

```sh
uci show dhcp
uci show network
```

### resolv 파일 확인

```sh
cat /tmp/resolv.conf.d/resolv.conf.auto
cat /etc/resolv.conf
```

### 로그 확인

```sh
logread | grep dnsmasq
logread | grep DNS
```

### 라우터에서 직접 DNS 조회

```sh
nslookup google.com
```

### 클라이언트 lease 확인

```sh
cat /tmp/dhcp.leases
```

확인할 항목:

- 클라이언트가 DHCP로 어떤 DNS 서버를 받는지
- OpenWrt가 상위 DNS 서버를 제대로 받았는지
- WAN 인터페이스가 정상인지
- dnsmasq가 실행 중인지
- LAN 클라이언트가 공유기 IP를 DNS 서버로 사용하는지

---

## Packet Capture로 DNS 확인

명령어 출력만으로 부족하면 패킷 캡처를 통해 DNS 요청과 응답이 실제로 오가는지 확인할 수 있다.

### Linux tcpdump

```bash
sudo tcpdump -i <interface> -n port 53
```

정상적인 DNS 흐름:

```text
Client -> DNS Server: Query A google.com
DNS Server -> Client: Response A 142.250.x.x
```

### 특정 DNS 서버와의 통신 확인

```bash
sudo tcpdump -i <interface> -n host 8.8.8.8 and port 53
```

### 판단 기준

```text
DNS Query가 보이지 않음:
클라이언트가 DNS 요청을 보내지 않거나, 로컬 캐시에서 처리했거나, DNS 설정이 잘못되었을 수 있음.

DNS Query는 보이는데 Response가 없음:
DNS 서버 미응답, 방화벽 차단, 라우팅 문제 가능성.

Response가 NXDOMAIN:
도메인이 존재하지 않거나 DNS 서버가 그렇게 판단하고 있음.

Response가 SERVFAIL:
DNS 서버 내부 오류, DNSSEC, authoritative DNS 문제 가능성.

Response는 정상인데 브라우저 접속 실패:
DNS 이후 단계인 TCP, TLS, HTTP, 프록시, 방화벽 문제 가능성.
```

---

## 단계별 진단 절차

DNS 문제는 다음 순서로 진단하는 것이 좋다.

---

### 1단계: IP 통신 가능 여부 확인

먼저 DNS 이전에 기본 네트워크 연결이 되는지 확인한다.

```bash
ping 8.8.8.8
```

판단:

```text
성공:
외부 IP 통신은 가능하므로 DNS 문제 가능성을 볼 수 있음.

실패:
DNS 이전에 게이트웨이, 라우팅, NAT, 방화벽, DHCP 문제를 먼저 확인해야 함.
```

---

### 2단계: 도메인 이름 통신 확인

```bash
ping google.com
```

판단:

```text
8.8.8.8 ping 성공 + google.com ping 실패:
DNS 문제 가능성 높음.

google.com ping 성공:
DNS는 기본적으로 동작할 가능성이 높음.
```

주의:

일부 환경에서는 ICMP가 차단될 수 있으므로, ping만으로 확정하지 않는다.

---

### 3단계: DNS 조회 직접 확인

Windows/Linux 공통:

```bash
nslookup google.com
```

Linux:

```bash
dig google.com
```

판단:

```text
정상 IP 응답:
DNS 조회는 성공.

timeout:
DNS 서버 미응답 또는 방화벽 차단 가능성.

NXDOMAIN:
도메인 없음, 오타, DNS 캐시 문제 가능성.

SERVFAIL:
DNS 서버 내부 오류, DNSSEC, authoritative DNS 문제 가능성.
```

---

### 4단계: 현재 DNS 서버 확인

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
cat /etc/resolv.conf
resolvectl status
nmcli dev show
```

확인할 것:

- DNS 서버 주소가 있는가?
- DNS 서버가 예상한 주소인가?
- DHCP에서 받은 DNS인가?
- VPN 인터페이스 DNS가 우선 적용되는가?
- `/etc/resolv.conf`가 127.0.0.53인지?
- systemd-resolved가 실제 upstream DNS를 갖고 있는가?

---

### 5단계: 다른 DNS 서버로 비교 조회

```bash
nslookup google.com 8.8.8.8
nslookup google.com 1.1.1.1
dig google.com @8.8.8.8
dig google.com @1.1.1.1
```

판단:

```text
현재 DNS에서는 실패 + 8.8.8.8에서는 성공:
현재 DNS 서버 문제 가능성.

8.8.8.8에서도 실패:
도메인 문제, 네트워크 차단, 방화벽, 오타 가능성.

사내 DNS에서만 내부 도메인 성공:
내부 전용 도메인일 가능성.
```

---

### 6단계: DNS 캐시 초기화

Windows:

```cmd
ipconfig /flushdns
```

Linux:

```bash
sudo resolvectl flush-caches
```

브라우저도 함께 확인:

- 브라우저 재시작
- 시크릿 모드 테스트
- 다른 브라우저 테스트
- 브라우저 DNS 캐시 초기화

---

### 7단계: hosts 파일 확인

Windows:

```text
C:\Windows\System32\drivers\etc\hosts
```

Linux:

```bash
cat /etc/hosts
```

확인할 것:

- 문제 도메인이 수동으로 매핑되어 있는가?
- 127.0.0.1로 잘못 연결되어 있는가?
- 예전 서버 IP가 남아 있는가?
- 테스트용 항목이 삭제되지 않았는가?

---

### 8단계: 방화벽과 DNS 포트 확인

DNS는 일반적으로 UDP 53을 사용한다.

Linux:

```bash
sudo tcpdump -i <interface> -n port 53
sudo firewall-cmd --list-all
sudo ufw status verbose
```

판단:

```text
DNS 요청이 나가지 않음:
클라이언트 설정 또는 로컬 방화벽 문제.

DNS 요청은 나가는데 응답이 없음:
DNS 서버, 중간 방화벽, 네트워크 경로 문제.

DNS 응답은 오는데 애플리케이션이 실패:
브라우저, 프록시, TLS, 애플리케이션 문제.
```

---

### 9단계: VPN, 프록시, 보안 프로그램 확인

확인할 것:

- VPN 연결 여부
- VPN 연결 시 DNS 서버 변경 여부
- split tunneling 설정
- proxy 설정
- 브라우저 DoH 설정
- 보안 프로그램의 DNS 보호 기능
- 회사/학교 네트워크 정책

Windows:

```cmd
ipconfig /all
route print
```

Linux:

```bash
resolvectl status
ip route
nmcli dev show
```

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
ping 8.8.8.8 성공 + ping google.com 실패:
DNS 문제 가능성이 높다.

ping 8.8.8.8 실패:
DNS 이전에 gateway, routing, NAT, firewall, DHCP 문제를 먼저 확인해야 한다.

nslookup google.com 실패:
DNS 서버 설정, DNS 서버 응답, 방화벽, 도메인 문제 가능성이 있다.

nslookup google.com 8.8.8.8 성공 + 기본 DNS 실패:
현재 설정된 DNS 서버 문제 가능성이 높다.

모든 DNS 서버에서 특정 도메인 조회 실패:
도메인 오타, 도메인 만료, authoritative DNS 문제 가능성이 있다.

특정 도메인만 실패:
도메인 레코드, DNS 캐시, 보안 정책, 내부/외부 DNS 차이 가능성이 있다.

내부 도메인만 실패:
사내 DNS, VPN DNS, search domain, split DNS 문제 가능성이 있다.

IP 주소가 169.254.x.x:
DNS 문제가 아니라 DHCP 문제 가능성이 높다.

DNS 서버 주소가 없음:
DHCP DNS option 누락 또는 클라이언트 DNS 설정 문제 가능성이 있다.

DNS 서버가 공유기 IP인데 조회 실패:
공유기 DNS 프록시, WAN DNS, 공유기 캐시 문제 가능성이 있다.

nslookup은 성공하지만 브라우저 접속 실패:
DNS보다는 HTTP/HTTPS, 프록시, 방화벽, TLS, 웹 서버 문제 가능성이 높다.

dig 결과가 NXDOMAIN:
도메인이 없거나 오타, DNS 캐시 문제 가능성이 있다.

dig 결과가 SERVFAIL:
DNS 서버 내부 오류, DNSSEC, authoritative DNS 문제 가능성이 있다.

resolv.conf가 127.0.0.53:
systemd-resolved 환경에서는 정상일 수 있으며, 실제 DNS 서버는 resolvectl status로 확인해야 한다.

VPN 연결 후 DNS 문제 발생:
VPN DNS push, split DNS, DNS 우선순위 문제 가능성이 있다.
```

---

## 문제 유형별 해결 방법

### IP는 되지만 도메인이 안 될 때

증상:

```text
ping 8.8.8.8 성공
ping google.com 실패
```

해결 절차:

1. 현재 DNS 서버 확인
2. `nslookup google.com` 실행
3. `nslookup google.com 8.8.8.8`로 비교
4. DNS 캐시 초기화
5. DHCP로 DNS를 다시 받기
6. 수동 DNS 임시 설정 후 비교
7. 방화벽에서 UDP 53 차단 여부 확인

Windows:

```cmd
ipconfig /all
nslookup google.com
nslookup google.com 8.8.8.8
ipconfig /flushdns
```

Linux:

```bash
cat /etc/resolv.conf
resolvectl status
dig google.com
dig google.com @8.8.8.8
sudo resolvectl flush-caches
```

---

### DNS 서버 주소가 없을 때

증상:

```text
IP 주소 있음
게이트웨이 있음
DNS 서버 없음
도메인 접속 실패
```

해결:

1. DHCP 서버에서 DNS option 확인
2. 클라이언트가 DHCP DNS를 무시하도록 설정되어 있는지 확인
3. NetworkManager의 `ipv4.ignore-auto-dns` 확인
4. 수동 DNS 설정 후 테스트
5. DHCP 재요청

Linux 예시:

```bash
nmcli dev show
nmcli con show "<connection-name>" | grep dns
sudo nmcli con mod "<connection-name>" ipv4.ignore-auto-dns no
sudo nmcli con up "<connection-name>"
```

---

### `/etc/resolv.conf`가 이상할 때

증상:

```text
nameserver가 없음
잘못된 nameserver가 있음
127.0.0.53만 있음
파일을 수정해도 계속 바뀜
```

해결:

1. systemd-resolved 사용 여부 확인
2. `resolvectl status`로 실제 DNS 확인
3. NetworkManager DNS 설정 확인
4. 직접 파일 수정 대신 네트워크 관리 도구에서 설정 변경
5. 필요 시 systemd-resolved 또는 NetworkManager 재시작

명령어:

```bash
cat /etc/resolv.conf
resolvectl status
systemctl status systemd-resolved
nmcli dev show
```

---

### 특정 도메인만 안 될 때

해결 절차:

1. 도메인 오타 확인
2. 기본 DNS에서 조회
3. 8.8.8.8, 1.1.1.1에서 조회 비교
4. hosts 파일 확인
5. DNS 캐시 초기화
6. 다른 네트워크에서 접속 테스트
7. 내부 도메인인지 확인
8. DNSSEC 또는 authoritative DNS 문제 확인

명령어:

```bash
dig target-domain.com
dig target-domain.com @8.8.8.8
dig target-domain.com @1.1.1.1
dig NS target-domain.com
dig +trace target-domain.com
```

---

### 내부 도메인이 안 될 때

해결 절차:

1. VPN 연결 여부 확인
2. 내부 DNS 서버 주소 확인
3. 내부 DNS 서버를 직접 지정해 조회
4. search domain 확인
5. split DNS 설정 확인
6. DHCP 또는 VPN이 DNS 정보를 제대로 배포하는지 확인

명령어:

```bash
resolvectl status
nmcli dev show
nslookup internal-domain <internal_dns_ip>
```

Windows:

```cmd
ipconfig /all
nslookup internal-domain <internal_dns_ip>
```

---

### 공유기 DNS가 문제일 때

증상:

```text
DNS 서버가 192.168.0.1 또는 192.168.1.1
공유기 DNS에서는 실패
8.8.8.8에서는 성공
```

해결:

1. 공유기 재부팅
2. 공유기 WAN DNS 확인
3. 공유기 DHCP DNS 설정 확인
4. 클라이언트에서 임시로 8.8.8.8 또는 1.1.1.1 설정
5. OpenWrt라면 dnsmasq 재시작
6. 공유기 로그 확인

OpenWrt:

```sh
/etc/init.d/dnsmasq restart
logread | grep dnsmasq
uci show dhcp
uci show network
```

---

### VPN 연결 후 DNS가 안 될 때

해결:

1. VPN 연결 전후 DNS 서버 비교
2. VPN 인터페이스 DNS 우선순위 확인
3. 내부 도메인이면 VPN DNS를 사용하는지 확인
4. 일반 인터넷 도메인이면 split tunneling 정책 확인
5. VPN 해제 후 DNS 설정이 원복되는지 확인
6. DNS 캐시 초기화

Windows:

```cmd
ipconfig /all
route print
nslookup google.com
```

Linux:

```bash
resolvectl status
ip route
nmcli dev show
```

---

## 에이전트 응답 전략

DNS 문제로 의심될 때 에이전트는 바로 DNS 서버를 바꾸라고만 말하면 안 된다. 먼저 IP 통신이 가능한지 확인해야 한다.

우선 물어볼 정보:

```text
1. 사용 중인 OS가 Windows인지 Linux인지
2. 유선인지 Wi-Fi인지
3. 모든 사이트가 안 되는지, 특정 사이트만 안 되는지
4. IP 주소로 ping이 되는지
5. 도메인 이름으로 ping이 되는지
6. nslookup 결과가 어떻게 나오는지
7. 현재 DNS 서버 주소가 무엇인지
8. VPN 또는 프록시 사용 중인지
9. 회사/학교/집/가상머신 중 어떤 환경인지
```

우선 요청할 명령어:

Windows:

```cmd
ipconfig /all
ping 8.8.8.8
ping google.com
nslookup google.com
```

Linux:

```bash
ip route
cat /etc/resolv.conf
resolvectl status
ping 8.8.8.8
ping google.com
dig google.com
```

상황에 따라 추가할 명령어:

```bash
dig google.com @8.8.8.8
dig google.com @1.1.1.1
sudo tcpdump -i <interface> -n port 53
```

---

## 에이전트 응답 예시

### 예시 1: IP ping은 되는데 도메인 ping이 안 되는 경우

사용자 입력:

```text
ping 8.8.8.8은 되는데 ping google.com은 안 돼
```

에이전트 응답:

```text
8.8.8.8로 ping이 된다는 것은 외부 IP까지의 기본 통신은 가능하다는 뜻입니다. 그런데 google.com 같은 도메인 이름으로 ping이 안 된다면 DNS 조회가 실패하고 있을 가능성이 높습니다.

먼저 아래를 확인하세요.

Windows라면:
`ipconfig /all`
`nslookup google.com`
`nslookup google.com 8.8.8.8`

Linux라면:
`cat /etc/resolv.conf`
`resolvectl status`
`dig google.com`
`dig google.com @8.8.8.8`

만약 기본 DNS에서는 실패하지만 8.8.8.8을 직접 지정했을 때 성공한다면, 현재 설정된 DNS 서버나 공유기 DNS 프록시에 문제가 있을 가능성이 큽니다.
```

---

### 예시 2: `/etc/resolv.conf`에 127.0.0.53만 보이는 경우

사용자 입력:

```text
cat /etc/resolv.conf 했는데 nameserver 127.0.0.53만 나와
```

에이전트 응답:

```text
Linux에서 `nameserver 127.0.0.53`이 보인다고 해서 무조건 문제는 아닙니다. 이 주소는 systemd-resolved가 사용하는 로컬 stub resolver일 수 있습니다.

이 경우 실제로 어떤 DNS 서버를 upstream으로 사용하는지는 아래 명령어로 확인해야 합니다.

`resolvectl status`

또는 구버전 환경에서는:

`systemd-resolve --status`

여기에서 Link별 DNS Servers나 Current DNS Server 항목을 확인하세요. 만약 실제 DNS 서버가 비어 있거나 예상과 다른 주소라면 DHCP DNS 옵션, NetworkManager 설정, VPN DNS 설정 문제일 수 있습니다.
```

---

### 예시 3: 특정 사이트만 안 되는 경우

사용자 입력:

```text
다른 사이트는 되는데 특정 사이트만 안 열려
```

에이전트 응답:

```text
특정 사이트만 안 열린다면 전체 DNS 장애보다는 해당 도메인의 DNS 레코드, 캐시, 보안 정책, 내부/외부 DNS 차이 문제일 가능성이 있습니다.

먼저 같은 도메인을 여러 DNS 서버로 비교 조회해보세요.

`nslookup example.com`
`nslookup example.com 8.8.8.8`
`nslookup example.com 1.1.1.1`

Linux라면:

`dig example.com`
`dig example.com @8.8.8.8`
`dig example.com @1.1.1.1`

기본 DNS에서만 실패하고 외부 DNS에서는 성공하면 현재 DNS 서버의 캐시나 정책 문제일 가능성이 있습니다. 반대로 모든 DNS에서 실패하면 도메인 오타, 도메인 만료, authoritative DNS 문제일 수 있습니다.
```

---

### 예시 4: nslookup은 되는데 브라우저가 안 되는 경우

사용자 입력:

```text
nslookup google.com은 되는데 브라우저에서는 사이트가 안 열려
```

에이전트 응답:

```text
nslookup이 정상적으로 IP를 반환한다면 DNS 조회 자체는 성공한 것입니다. 이 경우 문제는 DNS보다는 그 이후 단계인 TCP 연결, HTTPS, 프록시, 브라우저 캐시, 방화벽, 보안 프로그램 쪽일 가능성이 높습니다.

다음 순서로 확인하세요.

1. 다른 브라우저에서도 같은지 확인
2. 시크릿 모드에서 접속 테스트
3. 프록시 설정 확인
4. VPN 또는 보안 프로그램 잠시 해제 후 비교
5. `curl -I https://google.com`으로 HTTP/HTTPS 응답 확인
6. 방화벽 또는 회사/학교 보안 정책 확인

즉, 이 상황에서는 DNS 문서뿐 아니라 firewall_ports 또는 gateway_routing 문서도 함께 참고해야 합니다.
```

---

### 예시 5: VPN 연결 후 내부 도메인이 안 되는 경우

사용자 입력:

```text
VPN 연결했는데 사내 주소가 안 열려
```

에이전트 응답:

```text
VPN 연결 후 사내 도메인이 안 열린다면 VPN이 내부 DNS 서버 정보를 제대로 전달하지 못했거나, split DNS 설정이 잘못되었을 가능성이 있습니다.

먼저 VPN 연결 상태에서 DNS 서버가 어떻게 바뀌었는지 확인하세요.

Windows:
`ipconfig /all`
`nslookup 사내도메인 <사내DNS서버IP>`

Linux:
`resolvectl status`
`nmcli dev show`
`dig 사내도메인 @<사내DNS서버IP>`

사내 DNS 서버를 직접 지정했을 때 조회가 성공한다면, VPN DNS 우선순위나 search domain 설정 문제일 가능성이 높습니다.
```

---

## 주의할 점

DNS 문제를 진단할 때 다음을 주의해야 한다.

1. "인터넷이 안 된다"는 말만 듣고 DNS 문제로 단정하면 안 된다.
2. 먼저 IP 주소, 게이트웨이, 외부 IP 통신 가능 여부를 확인해야 한다.
3. `ping 8.8.8.8` 실패는 DNS 이전의 네트워크 문제일 가능성이 높다.
4. `ping google.com` 실패만으로 DNS 문제를 확정하지 말고 `nslookup` 또는 `dig`를 확인해야 한다.
5. `/etc/resolv.conf`의 `127.0.0.53`은 systemd-resolved 환경에서는 정상일 수 있다.
6. nslookup은 성공하지만 브라우저가 실패하면 DNS 이후 단계의 문제일 수 있다.
7. 특정 도메인만 실패하면 도메인 자체, 캐시, 내부 DNS, 보안 정책 문제를 고려해야 한다.
8. 내부 도메인은 외부 DNS에서 조회되지 않는 것이 정상일 수 있다.
9. VPN은 DNS 서버와 search domain을 변경할 수 있다.
10. 공유기 DNS 프록시가 문제일 때는 외부 DNS를 직접 지정하면 정상 동작할 수 있다.
11. hosts 파일은 DNS 서버 조회보다 우선될 수 있다.
12. DNS 캐시는 OS, 브라우저, 공유기, 사내 DNS 서버에 각각 존재할 수 있다.
13. DNS 서버를 무조건 8.8.8.8로 바꾸는 것은 사내망에서는 내부 도메인 접속을 깨뜨릴 수 있다.
14. 보안 정책상 외부 DNS 사용이 차단된 네트워크도 있다.
15. DNS 문제처럼 보여도 실제 원인은 방화벽, 프록시, TLS, 웹 서버 장애일 수 있다.

---

## 빠른 진단 요약

```text
1. ipconfig /all 또는 ip addr로 IP 설정 확인
2. 기본 게이트웨이 존재 여부 확인
3. ping 8.8.8.8로 외부 IP 통신 확인
4. ping google.com으로 도메인 통신 확인
5. nslookup google.com 또는 dig google.com 실행
6. 현재 DNS 서버 주소 확인
7. 8.8.8.8 또는 1.1.1.1을 직접 지정해 비교 조회
8. /etc/resolv.conf 또는 resolvectl status 확인
9. DNS 캐시 초기화
10. hosts 파일 확인
11. VPN, 프록시, 보안 프로그램 확인
12. 필요 시 tcpdump로 port 53 패킷 확인
```

---

## 핵심 키워드

DNS, DNS Troubleshooting, 도메인 접속 안 됨, IP로는 되는데 도메인 안 됨, ping 8.8.8.8 성공, ping google.com 실패, nslookup, dig, resolv.conf, systemd-resolved, resolvectl status, systemd-resolve --status, DNS 서버 주소, DNS Servers, nameserver, DNS cache, DNS 캐시, ipconfig /flushdns, resolvectl flush-caches, DNS_PROBE_FINISHED_NXDOMAIN, DNS_PROBE_FINISHED_NO_INTERNET, DNS_PROBE_FINISHED_BAD_CONFIG, NXDOMAIN, SERVFAIL, A record, AAAA record, CNAME, MX, TXT, NS, PTR, UDP 53, TCP 53, DNS over HTTPS, DNS over TLS, DoH, DoT, hosts file, /etc/hosts, Windows hosts, NetworkManager DNS, nmcli dev show, DHCP Option 6, 공유기 DNS, 사내 DNS, 내부 도메인, split DNS, VPN DNS, DNSSEC, authoritative DNS, recursive resolver, root DNS, TLD DNS, OpenWrt dnsmasq, tcpdump port 53.