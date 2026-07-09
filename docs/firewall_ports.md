# Firewall and Port Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 방화벽, 포트, 서비스 리스닝, 포트 포워딩, 클라우드 보안 그룹, 네트워크 ACL 관련 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

방화벽 또는 포트 문제는 보통 네트워크 연결 자체는 가능하지만 특정 서비스 접속만 실패할 때 의심할 수 있다. 예를 들어 서버에 `ping`은 되지만 SSH, HTTP, HTTPS, MySQL, PostgreSQL, Redis 같은 특정 서비스 접속이 안 되는 경우가 대표적이다.

사용자는 보통 다음처럼 표현한다.

- 서버는 살아 있는데 접속이 안 된다
- ping은 되는데 SSH가 안 된다
- 웹 서버를 띄웠는데 외부에서 안 열린다
- localhost에서는 되는데 다른 PC에서는 안 된다
- Connection refused가 뜬다
- Connection timeout이 뜬다
- 포트를 열었는데 접속이 안 된다
- 방화벽 문제인지 모르겠다

에이전트는 사용자의 증상을 듣고 먼저 다음을 구분해야 한다.

- 서버까지 IP 통신이 가능한 문제인지
- 서비스 프로세스가 실제로 실행 중인지
- 서비스가 올바른 포트에서 listen 중인지
- 서비스가 `127.0.0.1`에만 바인딩되어 있는지
- 서버 OS 방화벽이 차단하는지
- 클라우드 보안 그룹이나 네트워크 ACL이 차단하는지
- 공유기 또는 NAT 포트포워딩이 잘못되었는지
- 중간 네트워크 장비가 차단하는지
- 서버 내부에서는 되지만 외부에서는 안 되는 문제인지
- IPv4/IPv6 바인딩 차이인지
- Docker, VM, WSL 같은 가상화 네트워크 문제인지

방화벽/포트 문제를 정확히 판단하려면 `서비스 실행 상태`, `리스닝 포트`, `바인딩 주소`, `서버 방화벽`, `클라우드 보안 정책`, `NAT/포트포워딩`, `클라이언트에서의 접속 오류 메시지`, `패킷 도착 여부`를 함께 확인해야 한다.

---

## 관련 사용자 표현

사용자는 방화벽이나 포트라는 용어를 직접 말하지 않을 수도 있다. 다음 표현은 firewall 또는 port 문제와 관련될 가능성이 있다.

- ping은 되는데 접속이 안 돼
- SSH 접속이 안 돼
- HTTP 접속이 안 돼
- 웹페이지가 안 열려
- 서버는 켜져 있는데 외부에서 안 들어가져
- localhost에서는 되는데 외부에서는 안 돼
- 내 컴퓨터에서는 되는데 다른 컴퓨터에서는 안 돼
- 같은 서버 안에서는 접속되는데 밖에서는 안 돼
- connection refused가 떠
- connection timed out이 떠
- timeout만 나와
- 포트가 막힌 것 같아
- 방화벽을 열어야 하나?
- 22번 포트가 안 열려
- 80번 포트가 안 열려
- 443 포트 접속이 안 돼
- MySQL 접속이 안 돼
- Redis 접속이 안 돼
- FastAPI 서버는 실행했는데 접속이 안 돼
- Flask는 켰는데 다른 PC에서 안 보여
- uvicorn은 실행 중인데 외부 접속이 안 돼
- Docker 컨테이너 포트를 열었는데 안 돼
- 포트포워딩 했는데 외부에서 접속이 안 돼
- 공유기에서 포트 열었는데 안 돼
- 클라우드 서버에 접속이 안 돼
- 보안 그룹 열었는데도 안 돼
- 서버 내부 curl은 되는데 외부 curl은 안 돼
- telnet 접속이 안 돼
- nc가 실패해
- nmap에서 filtered라고 떠
- 방화벽 꺼야 돼?
- firewalld에서 포트 여는 법
- ufw에서 포트 여는 법
- Windows 방화벽에서 포트 여는 법
- 외부 IP로 접속이 안 돼
- 공인 IP로 접속이 안 돼
- 사설 IP로는 되는데 공인 IP로는 안 돼

---

## 핵심 개념

네트워크 서비스에 접속하려면 다음 조건이 모두 만족되어야 한다.

```text
1. 서버가 켜져 있어야 한다.
2. 서버까지 IP 경로가 있어야 한다.
3. 서비스 프로세스가 실행 중이어야 한다.
4. 서비스가 특정 포트에서 listen 중이어야 한다.
5. 서비스가 외부 접속 가능한 주소에 바인딩되어 있어야 한다.
6. 서버 OS 방화벽이 해당 포트를 허용해야 한다.
7. 클라우드 보안 그룹 또는 네트워크 ACL이 허용해야 한다.
8. NAT 또는 포트포워딩이 올바르게 설정되어야 한다.
9. 중간 네트워크 장비가 차단하지 않아야 한다.
10. 클라이언트가 올바른 IP와 포트로 접속해야 한다.
```

이 중 하나라도 실패하면 사용자는 "접속이 안 된다"고 느낄 수 있다.

방화벽/포트 문제는 다음과 같은 상황에서 특히 자주 발생한다.

- SSH 서버 구축
- 웹 서버 배포
- FastAPI/Flask 개발 서버 외부 접속
- MySQL/PostgreSQL 원격 접속
- Redis 원격 접속
- Docker 컨테이너 포트 매핑
- 클라우드 VM 접속
- 공유기 포트포워딩
- 사내망 방화벽 정책
- WSL/VirtualBox/VMware 네트워크 실습
- OpenWrt 포트포워딩
- 내부 서버를 외부에서 접속하려는 경우

---

## 포트와 서비스의 관계

포트는 하나의 장비 안에서 여러 네트워크 서비스를 구분하기 위한 번호이다.

예를 들어 하나의 서버가 다음 서비스를 동시에 제공할 수 있다.

```text
SSH   -> TCP 22
HTTP  -> TCP 80
HTTPS -> TCP 443
MySQL -> TCP 3306
Redis -> TCP 6379
FastAPI/Uvicorn -> TCP 8000
Flask -> TCP 5000
React/Vite -> TCP 5173
```

클라이언트가 서버에 접속할 때는 IP 주소와 포트 번호를 함께 사용한다.

```text
192.168.1.10:22
192.168.1.10:80
192.168.1.10:8000
```

즉, `ping 192.168.1.10`이 된다고 해서 `192.168.1.10:22` 또는 `192.168.1.10:80` 접속이 된다는 뜻은 아니다.

`ping`은 ICMP 기반이고, SSH/HTTP/MySQL은 TCP 기반이다. 서로 다른 프로토콜이므로 `ping` 성공은 서버까지의 기본 IP 도달성만 확인할 뿐, 특정 포트가 열려 있다는 보장은 하지 않는다.

---

## TCP 접속 흐름

대부분의 서비스 접속 문제는 TCP 연결 과정과 관련된다.

TCP 연결은 기본적으로 3-way handshake로 시작한다.

```text
Client -> Server: SYN
Server -> Client: SYN-ACK
Client -> Server: ACK
```

이 과정에서 문제가 발생하면 오류 메시지가 다르게 나타난다.

```text
SYN을 보냈는데 응답이 없음:
timeout 또는 filtered 가능성

SYN을 보냈는데 RST가 옴:
connection refused 가능성

SYN-ACK가 오고 ACK까지 완료됨:
TCP 연결은 성공

TCP 연결은 성공했지만 애플리케이션 응답 없음:
서비스 내부 문제, 인증 문제, 애플리케이션 계층 문제 가능성
```

따라서 포트 문제를 진단할 때는 단순히 "안 된다"가 아니라 `refused`, `timeout`, `filtered`, `no route`, `permission denied` 등을 구분해야 한다.

---

## 주요 오류 메시지의 의미

### 1. Connection refused

`Connection refused`는 보통 서버에 도달은 했지만 해당 포트에서 연결을 받아주는 프로세스가 없거나, 서버가 TCP RST로 거부한 경우에 발생한다.

대표 원인:

- 서비스가 실행 중이지 않음
- 서비스가 해당 포트에서 listen 중이지 않음
- 서비스가 `127.0.0.1`에만 바인딩됨
- 잘못된 포트로 접속함
- 방화벽이 reject 방식으로 거부함
- 컨테이너 포트 매핑이 없음
- 서버가 해당 포트를 닫아둠

예시:

```text
ssh: connect to host 192.168.1.10 port 22: Connection refused
curl: Failed to connect to 192.168.1.10 port 8000: Connection refused
```

판단:

```text
Connection refused는 서버까지 패킷이 도착했을 가능성이 높다.
따라서 라우팅 문제보다는 서비스 리스닝 상태, 포트 번호, 바인딩 주소, 방화벽 reject 정책을 먼저 확인한다.
```

---

### 2. Connection timed out

`Connection timed out`은 클라이언트가 접속 요청을 보냈지만 일정 시간 안에 응답을 받지 못한 경우이다.

대표 원인:

- 서버 OS 방화벽이 drop
- 클라우드 보안 그룹이 차단
- 네트워크 ACL이 차단
- 중간 방화벽이 차단
- 라우팅 경로 문제
- NAT/포트포워딩 누락
- 서버가 꺼져 있음
- 잘못된 공인 IP로 접속
- ISP 또는 학교/회사망에서 포트 차단
- 서버가 private subnet에 있음
- Docker/VM 네트워크가 외부에 노출되지 않음

예시:

```text
ssh: connect to host 203.0.113.10 port 22: Connection timed out
curl: Failed to connect to 203.0.113.10 port 80: Operation timed out
```

판단:

```text
Timeout은 중간에서 패킷이 버려지거나 응답이 돌아오지 않는 상황이다.
방화벽, 보안 그룹, NAT, 라우팅, 포트포워딩을 우선 확인한다.
```

---

### 3. No route to host

`No route to host`는 클라이언트가 목적지로 갈 경로를 찾지 못하거나, 중간 네트워크에서 도달 불가 메시지를 받은 경우에 발생할 수 있다.

대표 원인:

- 라우팅 테이블 문제
- 기본 게이트웨이 없음
- 목적지 네트워크로 가는 경로 없음
- 서버가 다른 네트워크에 있음
- 방화벽이 ICMP unreachable 반환
- VPN 경로 문제
- 잘못된 서브넷 마스크

진단:

```bash
ip route
route print
traceroute <server_ip>
tracert <server_ip>
```

이 경우 firewall_ports 문서뿐 아니라 gateway_routing 문서도 함께 참고해야 한다.

---

### 4. Permission denied

`Permission denied`는 네트워크 포트 연결 자체보다 인증 또는 권한 문제일 가능성이 높다.

대표 상황:

```text
SSH Permission denied
MySQL Access denied
PostgreSQL no pg_hba.conf entry
Redis NOAUTH Authentication required
HTTP 403 Forbidden
```

판단:

```text
Permission denied는 포트가 막힌 문제가 아니라 서비스까지는 도달했지만 인증, 계정, 권한, 서비스 설정에서 거부된 경우가 많다.
```

---

### 5. Network is unreachable

클라이언트가 목적지 네트워크로 갈 경로 자체를 모를 때 발생할 수 있다.

대표 원인:

- 클라이언트 IP 설정 문제
- 기본 게이트웨이 없음
- VPN 라우트 누락
- 인터페이스 down
- 잘못된 라우팅 테이블
- IPv6 경로 문제

이 경우 방화벽보다 IP 설정과 라우팅을 먼저 확인한다.

---

## 포트 상태 개념

포트 진단 시 포트 상태를 구분해야 한다.

### Open

해당 포트에서 서비스가 listen 중이고, 클라이언트가 연결할 수 있는 상태이다.

```text
포트 열림
서비스 실행 중
방화벽 허용
```

### Closed

서버에는 도달했지만 해당 포트에 서비스가 없어서 거부되는 상태이다.

```text
Connection refused
TCP RST
서비스 미실행 가능성
```

### Filtered

방화벽이나 보안 장비가 패킷을 drop하여 응답이 없는 상태이다.

```text
Connection timed out
nmap filtered
방화벽 또는 ACL 차단 가능성
```

### Listening

서버 내부에서 특정 프로세스가 해당 포트를 열고 연결을 기다리는 상태이다.

Linux:

```bash
ss -tulnp
```

Windows:

```cmd
netstat -ano
```

---

## 바인딩 주소의 중요성

서비스가 실행 중이어도 어떤 주소에 바인딩되어 있는지에 따라 외부 접속 가능 여부가 달라진다.

### 127.0.0.1에만 바인딩

```text
127.0.0.1:8000
localhost:8000
```

이 경우 서버 자기 자신에서는 접속 가능하지만, 외부 PC에서는 접속할 수 없다.

예시:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
flask run --host 127.0.0.1 --port 5000
```

증상:

```text
서버 내부에서 curl localhost:8000 성공
외부에서 http://server_ip:8000 실패
```

해결:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
flask run --host 0.0.0.0 --port 5000
```

### 0.0.0.0에 바인딩

```text
0.0.0.0:8000
```

모든 IPv4 인터페이스에서 연결을 받을 수 있다는 의미이다.

단, `0.0.0.0`에 바인딩했다고 해서 무조건 외부 접속이 되는 것은 아니다. 방화벽, 보안 그룹, NAT, 포트포워딩도 열려 있어야 한다.

### 특정 IP에만 바인딩

```text
192.168.1.10:8000
```

해당 인터페이스 IP로 들어오는 연결만 받을 수 있다.

### IPv6 바인딩

```text
:::
```

IPv6 전체 주소에 바인딩된 상태이다. 환경에 따라 IPv4도 함께 받을 수 있지만, OS 설정에 따라 다를 수 있다.

진단 시 `ss -tulnp` 출력의 Local Address를 반드시 확인해야 한다.

---

## 프로토콜 구분: TCP와 UDP

포트는 TCP와 UDP가 별도로 존재한다.

예를 들어 TCP 53과 UDP 53은 다르다.

```text
DNS: 주로 UDP 53, 일부 TCP 53
HTTP: TCP 80
HTTPS: TCP 443
SSH: TCP 22
DHCP: UDP 67/68
NTP: UDP 123
```

방화벽에서 TCP 포트만 열고 UDP 포트를 열지 않으면 UDP 기반 서비스는 동작하지 않을 수 있다.

예시:

```text
DNS 서버를 운영하는데 TCP 53만 허용하고 UDP 53을 막음
→ 일반 DNS 질의 실패 가능성
```

따라서 포트를 열 때는 반드시 프로토콜까지 확인해야 한다.

---

## 대표 서비스와 포트

```text
SSH: TCP 22
HTTP: TCP 80
HTTPS: TCP 443
DNS: UDP/TCP 53
DHCP Server: UDP 67
DHCP Client: UDP 68
MySQL/MariaDB: TCP 3306
PostgreSQL: TCP 5432
Redis: TCP 6379
MongoDB: TCP 27017
RDP: TCP 3389
SMB: TCP 445
FTP Control: TCP 21
SMTP: TCP 25
Submission: TCP 587
IMAP: TCP 143
IMAPS: TCP 993
POP3: TCP 110
NTP: UDP 123
Prometheus: TCP 9090
Grafana: TCP 3000
FastAPI/Uvicorn default: TCP 8000
Flask default: TCP 5000
React/Vite default: TCP 5173
Node.js dev server: TCP 3000 또는 5173 등
```

주의:

서비스의 기본 포트는 변경할 수 있다. 실제로 어떤 포트에서 실행 중인지는 반드시 서버에서 확인해야 한다.

---

## 방화벽/포트 문제의 대표 증상

### 1. ping은 되지만 특정 서비스 접속이 안 됨

가능한 원인:

- 서비스가 실행 중이지 않음
- 서비스가 다른 포트에서 실행 중
- 서버 방화벽이 해당 포트를 차단
- 클라우드 보안 그룹이 차단
- 서비스가 localhost에만 바인딩
- 애플리케이션 설정에서 외부 접속 차단
- 포트포워딩 누락
- 중간 네트워크 장비에서 차단

판단:

```text
ping 성공은 IP 도달성만 의미한다.
특정 포트 접속 가능 여부는 ss, netstat, nc, telnet, curl 등으로 별도 확인해야 한다.
```

---

### 2. SSH 접속만 안 됨

가능한 원인:

- sshd 서비스 미실행
- TCP 22 포트가 listen 중이 아님
- SSH 포트가 22가 아니라 다른 포트로 변경됨
- 서버 방화벽에서 22 차단
- 클라우드 보안 그룹에서 22 차단
- root 로그인 금지
- 비밀번호 로그인 금지
- 키 인증 문제
- fail2ban 또는 보안 정책 차단
- 접속 IP 제한
- NAT/포트포워딩 누락

진단:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
ssh -v user@server_ip
```

SSH 문제는 `ssh_troubleshooting.md` 문서도 함께 참고해야 한다.

---

### 3. HTTP/HTTPS 접속만 안 됨

가능한 원인:

- 웹 서버 미실행
- nginx/apache/uvicorn/flask 프로세스 미실행
- 80/443 포트 미리스닝
- 애플리케이션이 127.0.0.1에만 바인딩
- 방화벽에서 80/443 차단
- 클라우드 보안 그룹 차단
- HTTPS 인증서 문제
- reverse proxy 설정 문제
- SELinux 또는 권한 문제
- Docker 포트 매핑 누락

진단:

```bash
ss -tulnp | grep -E ':80|:443|:8000|:5000'
curl -I http://localhost
curl -I http://<server_ip>
sudo firewall-cmd --list-all
```

---

### 4. 서버 내부에서는 접속되지만 외부에서는 접속되지 않음

매우 중요한 증상이다.

예시:

```bash
curl http://localhost:8000
# 성공

curl http://192.168.1.10:8000
# 실패
```

가능한 원인:

- 서비스가 `127.0.0.1`에만 바인딩
- 서버 방화벽 차단
- 클라우드 보안 그룹 차단
- NAT/포트포워딩 누락
- 서버가 사설 IP만 가지고 있음
- 외부에서 접근 가능한 경로가 없음
- Docker 컨테이너 포트가 호스트로 publish되지 않음

판단 순서:

```text
1. 서버에서 ss -tulnp로 바인딩 주소 확인
2. 서버 내부에서 localhost 접속 확인
3. 서버 내부에서 server_ip 접속 확인
4. 같은 LAN의 다른 PC에서 접속 확인
5. 외부 인터넷에서 공인 IP로 접속 확인
6. 방화벽, 보안 그룹, NAT, 포트포워딩 확인
```

---

### 5. 외부에서는 안 되는데 같은 LAN에서는 됨

가능한 원인:

- 공유기 포트포워딩 누락
- 공인 IP가 아님
- CGNAT 환경
- ISP에서 포트 차단
- 공유기 WAN IP와 실제 공인 IP 불일치
- 서버가 사설 IP에만 존재
- 방화벽에서 외부 대역 차단
- 클라우드/IDC 네트워크 ACL 문제

확인:

```text
공유기 WAN IP와 외부에서 보이는 공인 IP가 같은지 확인
포트포워딩 대상 IP와 포트가 맞는지 확인
서버의 사설 IP가 바뀌지 않았는지 확인
```

---

### 6. 특정 포트만 접속 안 됨

가능한 원인:

- 해당 포트 서비스 미실행
- 방화벽에서 해당 포트만 차단
- 보안 그룹에서 해당 포트 미허용
- 애플리케이션이 다른 포트 사용
- 포트 충돌
- 운영체제 권한 문제
- ISP 또는 학교/회사망에서 특정 포트 차단

진단:

```bash
ss -tulnp
sudo firewall-cmd --list-all
nc -vz <server_ip> <port>
```

---

### 7. nmap에서 filtered로 표시됨

`filtered`는 보통 방화벽이나 필터링 장비가 응답을 차단하여 nmap이 포트 상태를 확정할 수 없다는 의미이다.

가능한 원인:

- 서버 방화벽 drop
- 클라우드 보안 그룹 차단
- 네트워크 ACL 차단
- 중간 방화벽 차단
- IDS/IPS 정책
- 라우터 ACL

판단:

```text
filtered는 서비스가 없는 것과 다르다.
방화벽 또는 필터링 장비에서 패킷을 버리고 있을 가능성이 높다.
```

---

## Possible Causes

방화벽/포트 문제의 원인은 크게 서비스 측, 서버 OS 방화벽, 클라우드/네트워크 정책, NAT/포트포워딩, 애플리케이션 설정, 가상화/컨테이너 환경으로 나눌 수 있다.

---

### 1. 서비스가 해당 포트에서 실행 중이지 않음

가장 먼저 확인해야 할 원인이다.

서버 방화벽을 확인하기 전에, 실제 서비스가 해당 포트에서 listen 중인지 확인해야 한다.

Linux:

```bash
ss -tulnp
```

특정 포트 확인:

```bash
ss -tulnp | grep ':22'
ss -tulnp | grep ':80'
ss -tulnp | grep ':8000'
```

Windows:

```cmd
netstat -ano
```

특정 포트 확인:

```cmd
netstat -ano | findstr :80
netstat -ano | findstr :22
netstat -ano | findstr :8000
```

판단:

```text
포트가 출력되지 않음:
서비스가 실행 중이지 않거나 다른 포트를 사용 중.

127.0.0.1:8000으로만 출력:
서버 내부에서만 접속 가능. 외부 접속 불가 가능성.

0.0.0.0:8000으로 출력:
모든 IPv4 인터페이스에서 listen 중. 방화벽이나 네트워크 정책 확인 필요.

192.168.1.10:8000으로 출력:
해당 IP로 들어오는 연결만 받을 수 있음.
```

---

### 2. 서버 방화벽이 포트를 차단

서버 자체 방화벽이 포트를 막으면 서비스가 실행 중이어도 외부 접속이 안 될 수 있다.

Linux에서는 주로 다음 도구가 사용된다.

- firewalld
- ufw
- iptables
- nftables

Windows에서는 Windows Defender Firewall이 사용된다.

서버 방화벽 문제는 보통 다음 증상을 만든다.

```text
서버 내부 localhost 접속 성공
서버 내부 server_ip 접속 성공 또는 실패
외부 클라이언트 접속 실패
nc/telnet timeout
nmap filtered
```

---

### 3. 클라우드 보안 그룹 또는 네트워크 ACL이 차단

AWS, Azure, GCP, Naver Cloud, Oracle Cloud 같은 클라우드 환경에서는 서버 OS 방화벽 외에도 클라우드 레벨의 보안 정책이 존재한다.

예시:

```text
AWS Security Group
AWS Network ACL
Azure NSG
GCP Firewall Rules
Naver Cloud ACG
Oracle Cloud Security List
```

증상:

```text
서버에서 서비스 정상 실행
서버 OS 방화벽도 열림
하지만 외부에서 timeout
```

판단:

```text
클라우드 VM은 OS 내부 방화벽만 열어서는 부족하다.
클라우드 콘솔에서 inbound rule도 허용해야 한다.
```

확인할 항목:

- 인바운드 TCP 포트 허용 여부
- 소스 IP 범위
- 프로토콜 TCP/UDP
- 서버가 연결된 subnet의 ACL
- public IP 연결 여부
- private subnet 여부
- route table에서 Internet Gateway/NAT Gateway 경로
- 인스턴스에 보안 그룹이 올바르게 연결되어 있는지

---

### 4. 서비스가 localhost에만 바인딩

개발 서버에서 매우 자주 발생한다.

예시:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
flask run
npm run dev
```

일부 개발 서버는 기본적으로 localhost에만 바인딩한다.

증상:

```text
서버 내부 localhost:8000 접속 성공
다른 PC에서 server_ip:8000 접속 실패
```

해결:

FastAPI/Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Flask:

```bash
flask run --host 0.0.0.0 --port 5000
```

Vite:

```bash
npm run dev -- --host 0.0.0.0
```

또는 `vite.config.js`에서 host 설정.

---

### 5. 포트포워딩이 잘못 설정됨

집이나 사무실 공유기 뒤에 있는 서버를 외부 인터넷에서 접속하려면 포트포워딩이 필요할 수 있다.

예시:

```text
외부 공인 IP: 203.0.113.10
공유기 내부 서버 IP: 192.168.0.50
외부 포트: 2222
내부 포트: 22
```

포트포워딩 설정:

```text
203.0.113.10:2222 -> 192.168.0.50:22
```

가능한 문제:

- 내부 서버 IP가 바뀜
- 포트포워딩 대상 IP가 틀림
- 외부 포트와 내부 포트를 혼동
- TCP/UDP 프로토콜 선택 오류
- 서버 방화벽 미허용
- 공유기 WAN IP가 실제 공인 IP가 아님
- CGNAT 환경
- 이중 NAT 구조
- ISP에서 포트 차단

확인할 항목:

```text
서버 내부 IP
공유기 포트포워딩 대상 IP
외부 포트
내부 포트
프로토콜 TCP/UDP
공유기 WAN IP
외부에서 보이는 공인 IP
```

---

### 6. 중간 네트워크 장비에서 포트 차단

회사, 학교, 공공기관, 데이터센터 네트워크에서는 중간 방화벽이나 보안 장비가 특정 포트를 차단할 수 있다.

가능한 장비:

- 라우터 ACL
- L3 스위치 ACL
- 방화벽
- IDS/IPS
- 웹 필터링 장비
- 프록시
- NAC
- 클라우드 네트워크 ACL

증상:

```text
서버와 서비스는 정상
서버 OS 방화벽도 허용
특정 네트워크에서만 접속 실패
다른 네트워크에서는 성공
```

예시:

```text
집에서는 접속됨
학교 Wi-Fi에서는 접속 안 됨
모바일 핫스팟에서는 접속됨
```

판단:

```text
네트워크 위치에 따라 결과가 다르면 중간 네트워크 정책 차단 가능성이 있다.
```

---

### 7. Docker 포트 매핑 문제

Docker 컨테이너 내부에서 서비스가 실행 중이어도 호스트 포트로 publish하지 않으면 외부에서 접근할 수 없다.

잘못된 예:

```bash
docker run myapp
```

이 경우 컨테이너 내부에서만 포트가 열려 있을 수 있다.

올바른 예:

```bash
docker run -p 8000:8000 myapp
```

의미:

```text
호스트 8000번 포트 -> 컨테이너 8000번 포트
```

확인:

```bash
docker ps
```

출력 예:

```text
0.0.0.0:8000->8000/tcp
```

주의:

컨테이너 안의 애플리케이션도 `0.0.0.0`에 바인딩해야 한다.

잘못된 경우:

```text
컨테이너 내부 앱이 127.0.0.1:8000에만 바인딩
호스트에서 포트 publish함
외부 접속 실패 가능성
```

해결:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

### 8. VM 또는 WSL 네트워크 문제

VirtualBox, VMware, Hyper-V, WSL 환경에서는 네트워크 모드에 따라 포트 접근 방식이 달라진다.

대표 모드:

```text
NAT
Bridge
Host-only
Internal Network
WSL NAT
```

증상:

```text
VM 내부에서는 서비스 접속 가능
호스트에서는 접속 안 됨
외부 PC에서는 접속 안 됨
```

가능한 원인:

- NAT 모드에서 포트포워딩 미설정
- Host-only 네트워크라 외부 접근 불가
- Bridge 대상 인터페이스 오류
- VM 내부 방화벽 차단
- WSL 포트 바인딩 문제
- Windows 방화벽 차단

VirtualBox NAT에서는 외부에서 VM으로 접속하려면 VirtualBox 포트포워딩이 필요하다.

예시:

```text
Host Port 2222 -> Guest Port 22
Host Port 8000 -> Guest Port 8000
```

Bridge 모드에서는 VM이 실제 LAN에 연결된 장비처럼 동작하므로, VM의 IP로 직접 접속할 수 있다. 단, VM 내부 방화벽은 여전히 확인해야 한다.

---

### 9. SELinux 정책 문제

Linux, 특히 RHEL/Rocky/CentOS/Fedora 계열에서는 SELinux가 서비스 동작을 제한할 수 있다.

증상:

```text
서비스 실행 중
포트도 listen 중
방화벽도 열림
하지만 서비스가 특정 포트 사용 또는 파일 접근에 실패
```

확인:

```bash
getenforce
sestatus
```

로그 확인:

```bash
sudo ausearch -m AVC -ts recent
sudo journalctl -t setroubleshoot --no-pager
```

주의:

SELinux를 무조건 끄는 것은 권장되지 않는다. 운영 환경에서는 필요한 policy나 boolean, port context를 설정하는 방식이 좋다.

HTTP 서비스가 비표준 포트를 사용할 때 예시:

```bash
sudo semanage port -a -t http_port_t -p tcp 8080
```

이미 등록된 경우 수정:

```bash
sudo semanage port -m -t http_port_t -p tcp 8080
```

---

### 10. 애플리케이션 자체 설정 문제

서비스별로 원격 접속 허용 설정이 따로 있을 수 있다.

예시:

MySQL/MariaDB:

```text
bind-address = 127.0.0.1
```

이 경우 외부 접속 불가.

해결 예시:

```text
bind-address = 0.0.0.0
```

또한 MySQL 계정도 원격 접속을 허용해야 한다.

```sql
'user'@'localhost' 와 'user'@'%' 는 다르다.
```

PostgreSQL:

```text
listen_addresses
pg_hba.conf
```

Redis:

```text
bind 127.0.0.1
protected-mode yes
```

SSH:

```text
PermitRootLogin
PasswordAuthentication
AllowUsers
Port
```

웹 서버:

```text
server_name
listen
reverse proxy
allowed hosts
CORS
```

즉, 포트가 열려 있어도 애플리케이션 설정에서 거부할 수 있다.

---

## Recommended Commands

방화벽/포트 문제는 운영체제별로 확인 명령어가 다르다.

---

## Linux 서버 진단 명령어

### 리스닝 포트 확인

```bash
ss -tulnp
```

옵션 의미:

```text
-t: TCP
-u: UDP
-l: listening
-n: 숫자 주소/포트로 표시
-p: 프로세스 표시
```

특정 포트 확인:

```bash
ss -tulnp | grep ':22'
ss -tulnp | grep ':80'
ss -tulnp | grep ':443'
ss -tulnp | grep ':8000'
```

### netstat 사용

일부 환경에서는 netstat을 사용할 수 있다.

```bash
netstat -tulnp
```

특정 포트 확인:

```bash
netstat -tulnp | grep ':80'
```

### 프로세스 확인

```bash
ps aux | grep nginx
ps aux | grep sshd
ps aux | grep uvicorn
```

### 특정 포트를 사용하는 프로세스 확인

```bash
sudo lsof -i :80
sudo lsof -i :8000
```

### 서비스 상태 확인

```bash
systemctl status sshd
systemctl status nginx
systemctl status apache2
systemctl status httpd
systemctl status mariadb
systemctl status mysql
```

### 서버 내부에서 접속 테스트

```bash
curl -I http://localhost
curl -I http://127.0.0.1:8000
curl -I http://<server_ip>:8000
```

### 클라이언트에서 포트 접속 테스트

```bash
nc -vz <server_ip> <port>
```

예시:

```bash
nc -vz 192.168.1.10 22
nc -vz 192.168.1.10 80
nc -vz 192.168.1.10 8000
```

### telnet으로 포트 테스트

```bash
telnet <server_ip> <port>
```

예시:

```bash
telnet 192.168.1.10 22
telnet 192.168.1.10 80
```

주의:

`telnet`은 설치되어 있지 않을 수 있다. 이 경우 `nc`를 사용하는 것이 좋다.

---

## firewalld 진단 명령어

RHEL, Rocky, CentOS, Fedora 계열에서는 firewalld를 사용하는 경우가 많다.

### firewalld 상태 확인

```bash
sudo systemctl status firewalld
```

### 현재 zone과 규칙 확인

```bash
sudo firewall-cmd --list-all
```

### 활성 zone 확인

```bash
sudo firewall-cmd --get-active-zones
```

### 특정 zone 확인

```bash
sudo firewall-cmd --zone=public --list-all
```

### 열려 있는 포트 확인

```bash
sudo firewall-cmd --list-ports
```

### 허용 서비스 확인

```bash
sudo firewall-cmd --list-services
```

### 포트 열기

예시: TCP 8000 허용

```bash
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### 서비스 단위로 허용

예시: HTTP 허용

```bash
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --reload
```

HTTPS 허용:

```bash
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --reload
```

SSH 허용:

```bash
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload
```

### 포트 제거

```bash
sudo firewall-cmd --remove-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

주의:

운영 환경에서는 필요한 포트만 열어야 한다. 임시 해결을 위해 방화벽 전체를 끄는 것은 위험하다.

---

## ufw 진단 명령어

Ubuntu 계열에서는 ufw를 사용하는 경우가 많다.

### 상태 확인

```bash
sudo ufw status verbose
```

### 포트 허용

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
```

### 특정 IP에서만 허용

```bash
sudo ufw allow from <client_ip> to any port 22 proto tcp
```

### 규칙 삭제

```bash
sudo ufw delete allow 8000/tcp
```

### ufw 활성화

```bash
sudo ufw enable
```

주의:

원격 SSH 접속 중 ufw를 활성화할 때는 반드시 SSH 포트를 먼저 허용해야 한다.

```bash
sudo ufw allow ssh
sudo ufw enable
```

그렇지 않으면 자신의 SSH 접속이 끊길 수 있다.

---

## iptables 진단 명령어

구형 Linux 또는 직접 방화벽을 구성한 환경에서는 iptables를 사용할 수 있다.

### 규칙 확인

```bash
sudo iptables -L -n -v
```

### NAT 테이블 확인

```bash
sudo iptables -t nat -L -n -v
```

### INPUT 체인 확인

```bash
sudo iptables -L INPUT -n -v
```

확인할 것:

```text
DROP 정책이 있는가?
특정 포트를 차단하는가?
특정 IP만 허용하는가?
기본 정책이 DROP인가?
```

---

## nftables 진단 명령어

최신 Linux에서는 nftables가 사용될 수 있다.

### 전체 ruleset 확인

```bash
sudo nft list ruleset
```

확인할 것:

```text
tcp dport 22 accept
tcp dport 80 accept
tcp dport 8000 accept
drop rule
reject rule
```

---

## Windows 서버/클라이언트 진단 명령어

### 리스닝 포트 확인

```cmd
netstat -ano
```

특정 포트 확인:

```cmd
netstat -ano | findstr :80
netstat -ano | findstr :443
netstat -ano | findstr :22
netstat -ano | findstr :8000
```

### PID로 프로세스 확인

```cmd
tasklist | findstr <PID>
```

### PowerShell에서 포트 테스트

```powershell
Test-NetConnection <server_ip> -Port <port>
```

예시:

```powershell
Test-NetConnection 192.168.1.10 -Port 22
Test-NetConnection 192.168.1.10 -Port 80
Test-NetConnection 192.168.1.10 -Port 8000
```

### Windows 방화벽 규칙 확인

PowerShell:

```powershell
Get-NetFirewallRule
```

특정 포트 허용 규칙 생성 예시:

```powershell
New-NetFirewallRule -DisplayName "Allow TCP 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Windows에서 현재 연결 확인

```cmd
netstat -ano
```

---

## 클라우드 보안 그룹 확인 항목

클라우드 환경에서는 콘솔에서 다음 항목을 확인해야 한다.

```text
Inbound Rules
Outbound Rules
Protocol
Port
Source IP
Security Group 연결 대상
Network ACL
Subnet Route Table
Public IP 연결 여부
Private/Public Subnet 여부
```

예시 인바운드 규칙:

```text
TCP 22   Source: 내 공인 IP/32
TCP 80   Source: 0.0.0.0/0
TCP 443  Source: 0.0.0.0/0
TCP 8000 Source: 내 공인 IP/32 또는 필요한 대역
```

주의:

```text
0.0.0.0/0으로 SSH를 여는 것은 보안상 위험하다.
가능하면 자신의 공인 IP만 허용한다.
```

---

## NAT와 포트포워딩 진단

공유기 뒤의 사설 IP 서버를 외부에서 접속하려면 포트포워딩이 필요하다.

### 확인할 항목

```text
서버 사설 IP
서버 서비스 포트
공유기 WAN IP
외부에서 보이는 공인 IP
포트포워딩 외부 포트
포트포워딩 내부 포트
프로토콜 TCP/UDP
서버 방화벽
```

### 포트포워딩 예시

```text
외부 포트 2222 -> 내부 IP 192.168.0.50, 내부 포트 22
외부 포트 8080 -> 내부 IP 192.168.0.50, 내부 포트 80
```

접속 예시:

```bash
ssh -p 2222 user@<public_ip>
curl http://<public_ip>:8080
```

### CGNAT 확인

공유기 WAN IP가 실제 공인 IP와 다르면 CGNAT 또는 이중 NAT일 수 있다.

판단:

```text
공유기 WAN IP: 100.64.x.x, 10.x.x.x, 172.16~31.x.x, 192.168.x.x
외부에서 보이는 IP와 공유기 WAN IP가 다름
```

이 경우 일반적인 포트포워딩으로는 외부 접속이 어려울 수 있다.

해결 방향:

```text
공인 IP 신청
클라우드 서버 사용
VPN 사용
Tailscale/ZeroTier 같은 오버레이 네트워크 사용
Reverse SSH Tunnel 사용
Cloudflare Tunnel 같은 터널 사용
```

---

## Docker 포트 진단 명령어

### 실행 중인 컨테이너 확인

```bash
docker ps
```

확인할 항목:

```text
PORTS
0.0.0.0:8000->8000/tcp
127.0.0.1:8000->8000/tcp
```

### 컨테이너 내부 접속

```bash
docker exec -it <container_name> sh
```

컨테이너 내부에서 포트 확인:

```bash
ss -tulnp
```

### 컨테이너 로그 확인

```bash
docker logs <container_name>
```

### 올바른 포트 매핑 예시

```bash
docker run -p 8000:8000 myapp
```

### localhost에만 publish된 경우

```text
127.0.0.1:8000->8000/tcp
```

이 경우 호스트 자기 자신에서는 접속 가능하지만 외부에서 접속이 안 될 수 있다.

---

## Packet Capture로 포트 확인

명령어 출력만으로 부족하면 tcpdump로 패킷이 서버에 도착하는지 확인할 수 있다.

### 서버에서 특정 포트 패킷 확인

```bash
sudo tcpdump -i <interface> -n port <port>
```

예시:

```bash
sudo tcpdump -i eth0 -n port 22
sudo tcpdump -i eth0 -n port 80
sudo tcpdump -i eth0 -n port 8000
```

### 특정 클라이언트와 포트 확인

```bash
sudo tcpdump -i eth0 -n host <client_ip> and port <port>
```

### TCP SYN 확인

```bash
sudo tcpdump -i eth0 -n 'tcp[tcpflags] & tcp-syn != 0'
```

### 판단 기준

```text
클라이언트가 접속 시도하는데 서버 tcpdump에 SYN이 보이지 않음:
패킷이 서버까지 도달하지 못함. 클라우드 보안 그룹, 네트워크 ACL, 라우팅, NAT, 중간 방화벽 문제 가능성.

서버 tcpdump에 SYN이 보이고 SYN-ACK를 보냄:
서버는 응답하고 있음. 클라이언트 쪽 방화벽, return path, 중간 네트워크 문제 가능성.

서버 tcpdump에 SYN이 보이고 RST가 나감:
해당 포트에 서비스가 없거나 거부 중. Connection refused 가능성.

SYN은 보이지만 응답이 없음:
서버 방화벽 drop 또는 커널/보안 정책 문제 가능성.

TCP 연결은 완료되지만 애플리케이션 응답이 없음:
서비스 내부 문제, 애플리케이션 설정, 인증, 프록시 문제 가능성.
```

---

## 단계별 진단 절차

방화벽/포트 문제는 다음 순서로 진단하는 것이 좋다.

---

### 1단계: 서버 IP 도달성 확인

클라이언트에서 서버 IP로 ping을 시도한다.

```bash
ping <server_ip>
```

판단:

```text
ping 성공:
IP 도달성은 어느 정도 있음. 포트/서비스 문제로 좁힐 수 있음.

ping 실패:
ICMP 차단일 수도 있지만, gateway/routing/firewall 문제 가능성도 있음.
```

주의:

ping 실패가 곧 서버 접속 불가를 의미하지는 않는다. ICMP가 차단되어도 TCP 포트는 열려 있을 수 있다.

---

### 2단계: 클라이언트에서 포트 접속 테스트

```bash
nc -vz <server_ip> <port>
```

또는:

```bash
telnet <server_ip> <port>
```

Windows PowerShell:

```powershell
Test-NetConnection <server_ip> -Port <port>
```

판단:

```text
succeeded:
포트 접속 가능.

connection refused:
서버에 도달했지만 해당 포트에서 서비스가 없거나 거부.

timed out:
방화벽, 보안 그룹, NAT, 라우팅 문제 가능성.

no route to host:
라우팅 또는 네트워크 도달성 문제 가능성.
```

---

### 3단계: 서버에서 서비스 리스닝 확인

Linux:

```bash
ss -tulnp
```

Windows:

```cmd
netstat -ano
```

확인할 것:

```text
해당 포트가 listen 중인가?
TCP인지 UDP인지 맞는가?
바인딩 주소가 127.0.0.1인가?
0.0.0.0인가?
특정 IP인가?
프로세스가 예상한 서비스인가?
```

---

### 4단계: 서버 내부에서 접속 테스트

서버 자체에서 확인한다.

```bash
curl -I http://localhost:<port>
curl -I http://127.0.0.1:<port>
curl -I http://<server_ip>:<port>
```

판단:

```text
localhost 성공 + server_ip 실패:
바인딩 주소 또는 서버 내부 방화벽 문제 가능성.

localhost 실패:
서비스 자체가 제대로 실행되지 않았을 가능성.

server_ip 성공 + 외부 실패:
서버 외부 방화벽, 보안 그룹, NAT, 중간 네트워크 문제 가능성.
```

---

### 5단계: 서버 OS 방화벽 확인

firewalld:

```bash
sudo firewall-cmd --list-all
```

ufw:

```bash
sudo ufw status verbose
```

iptables:

```bash
sudo iptables -L -n -v
```

nftables:

```bash
sudo nft list ruleset
```

Windows Firewall:

```powershell
Get-NetFirewallRule
```

---

### 6단계: 클라우드 보안 그룹 또는 네트워크 ACL 확인

클라우드 VM인 경우 콘솔에서 확인한다.

확인할 것:

```text
Inbound rule에 해당 포트가 있는가?
Source IP가 내 IP를 허용하는가?
프로토콜 TCP/UDP가 맞는가?
서버에 해당 보안 그룹이 연결되어 있는가?
Subnet ACL이 막고 있지 않은가?
Public IP가 있는가?
Route table에 인터넷 경로가 있는가?
```

---

### 7단계: NAT/포트포워딩 확인

공유기 뒤 서버라면 확인한다.

```text
외부 포트 -> 내부 IP:내부 포트
```

확인할 것:

```text
내부 서버 IP가 바뀌지 않았는가?
포트포워딩 대상 IP가 맞는가?
외부 포트와 내부 포트를 혼동하지 않았는가?
TCP/UDP가 맞는가?
공유기 WAN IP가 실제 공인 IP인가?
CGNAT 환경은 아닌가?
```

---

### 8단계: 패킷 캡처로 최종 확인

서버에서 tcpdump 실행 후 클라이언트가 접속 시도한다.

```bash
sudo tcpdump -i <interface> -n port <port>
```

판단:

```text
패킷이 안 보임:
서버 이전 경로 문제.

패킷은 보임:
서버 내부 방화벽, 서비스, 애플리케이션 문제.

SYN/RST:
서비스 미리스닝 또는 거부.

SYN만 반복:
방화벽 drop 또는 응답 경로 문제.
```

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
ping 성공 + 특정 포트 실패:
IP 도달성은 있으나 서비스, 포트, 방화벽 문제 가능성이 높다.

Connection refused:
서버에 도달했지만 해당 포트에서 서비스가 listen 중이 아니거나 reject되고 있을 가능성이 높다.

Connection timed out:
방화벽, 보안 그룹, ACL, NAT, 포트포워딩, 라우팅 문제 가능성이 높다.

서버 내부 localhost 접속 성공 + 외부 접속 실패:
바인딩 주소, 서버 방화벽, 보안 그룹, NAT 문제 가능성이 높다.

서버 내부 localhost 접속 실패:
서비스 자체가 실행되지 않았거나 애플리케이션 오류 가능성이 높다.

ss에서 127.0.0.1:<port>만 보임:
외부 접속 불가. 0.0.0.0 또는 서버 IP에 바인딩해야 한다.

ss에서 0.0.0.0:<port>가 보임 + 외부 접속 실패:
서비스는 외부 접속 가능한 형태로 listen 중이므로 방화벽, 보안 그룹, NAT를 확인해야 한다.

서버 tcpdump에 SYN이 안 보임:
패킷이 서버까지 도달하지 못함. 클라우드 보안 그룹, 네트워크 ACL, 포트포워딩, 중간 방화벽 가능성.

서버 tcpdump에 SYN이 보이고 RST가 나감:
서비스 미리스닝 또는 애플리케이션 거부 가능성.

서버 tcpdump에 SYN이 보이고 SYN-ACK도 나감:
서버는 응답하고 있으므로 클라이언트 방향 경로, 중간 장비, 클라이언트 방화벽을 확인한다.

클라우드 서버에서 OS 방화벽은 열었는데 여전히 timeout:
클라우드 보안 그룹 또는 네트워크 ACL을 확인해야 한다.

공유기 뒤 서버에서 LAN 접속은 되지만 외부 접속 실패:
포트포워딩, 공인 IP, CGNAT, 이중 NAT 문제 가능성이 높다.

Docker 컨테이너 내부에서는 되지만 호스트/외부에서 안 됨:
docker -p 포트 매핑, 컨테이너 앱 바인딩 주소, 호스트 방화벽 문제 가능성이 높다.
```

---

## 문제 유형별 해결 방법

### ping은 되는데 SSH가 안 될 때

1. SSH 서비스 상태 확인
2. 22번 포트 listen 확인
3. SSH 포트가 변경되었는지 확인
4. 서버 방화벽에서 SSH 허용 확인
5. 클라우드 보안 그룹에서 TCP 22 허용 확인
6. 접속 오류가 refused인지 timeout인지 확인
7. 인증 문제인지 포트 문제인지 구분

명령어:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
nc -vz <server_ip> 22
ssh -v user@<server_ip>
```

---

### 웹 서버를 띄웠는데 외부 접속이 안 될 때

1. 웹 서버 프로세스 실행 확인
2. 포트 listen 확인
3. 바인딩 주소 확인
4. 서버 내부 curl 확인
5. 서버 IP로 curl 확인
6. 방화벽에서 포트 허용
7. 클라우드 보안 그룹 확인
8. NAT/포트포워딩 확인

명령어:

```bash
ss -tulnp | grep -E ':80|:443|:8000|:5000'
curl -I http://localhost:8000
curl -I http://<server_ip>:8000
sudo firewall-cmd --list-all
```

FastAPI 예시:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Flask 예시:

```bash
flask run --host 0.0.0.0 --port 5000
```

---

### Connection refused가 발생할 때

1. 포트 번호가 맞는지 확인
2. 서비스가 실행 중인지 확인
3. 서비스가 해당 포트에서 listen 중인지 확인
4. 바인딩 주소 확인
5. 방화벽 reject 정책 확인
6. Docker/VM 포트 매핑 확인

명령어:

```bash
ss -tulnp
sudo lsof -i :<port>
systemctl status <service>
```

---

### Connection timed out이 발생할 때

1. 서버 IP가 맞는지 확인
2. 서버가 켜져 있는지 확인
3. 서버 방화벽 확인
4. 클라우드 보안 그룹 확인
5. 네트워크 ACL 확인
6. NAT/포트포워딩 확인
7. 중간 네트워크 차단 확인
8. tcpdump로 서버에 패킷 도착 여부 확인

명령어:

```bash
nc -vz <server_ip> <port>
sudo tcpdump -i <interface> -n port <port>
sudo firewall-cmd --list-all
```

---

### localhost에서는 되는데 외부에서는 안 될 때

1. `ss -tulnp`로 바인딩 주소 확인
2. `127.0.0.1`이면 `0.0.0.0`으로 변경
3. 서버 IP로 로컬 접속 테스트
4. 서버 방화벽 허용
5. 클라우드 보안 그룹 허용
6. 공유기 포트포워딩 확인

예시:

```bash
ss -tulnp | grep ':8000'
curl http://localhost:8000
curl http://<server_ip>:8000
```

---

### Docker 서비스가 외부에서 안 될 때

1. `docker ps`에서 포트 publish 확인
2. 컨테이너 내부 앱이 0.0.0.0에 바인딩되어 있는지 확인
3. 호스트 방화벽 확인
4. 클라우드 보안 그룹 확인
5. Docker 네트워크 모드 확인

명령어:

```bash
docker ps
docker logs <container_name>
docker exec -it <container_name> sh
ss -tulnp
```

실행 예:

```bash
docker run -p 8000:8000 myapp
```

---

### 클라우드 서버 포트가 안 열릴 때

1. 서버 내부에서 서비스 listen 확인
2. OS 방화벽 허용 확인
3. 클라우드 보안 그룹 inbound rule 확인
4. 네트워크 ACL 확인
5. public IP 연결 확인
6. subnet route table 확인
7. source IP 제한 확인

체크리스트:

```text
TCP/UDP 프로토콜이 맞는가?
포트 번호가 맞는가?
source IP가 내 IP를 허용하는가?
보안 그룹이 실제 인스턴스에 연결되어 있는가?
서버가 public subnet에 있는가?
```

---

## 에이전트 응답 전략

방화벽/포트 문제로 의심될 때 에이전트는 바로 "방화벽을 꺼라"라고 하면 안 된다. 먼저 서비스가 실제로 실행 중인지, 포트가 listen 중인지, 오류가 refused인지 timeout인지 구분해야 한다.

우선 물어볼 정보:

```text
1. 접속하려는 서비스 종류는 무엇인가? SSH, HTTP, MySQL, FastAPI 등
2. 접속하려는 서버 IP와 포트는 무엇인가?
3. 접속 오류가 connection refused인지 timeout인지?
4. 서버 내부에서는 접속되는가?
5. 같은 LAN의 다른 장비에서는 접속되는가?
6. 외부 인터넷에서 접속하려는 것인가?
7. 서버 OS는 Linux인지 Windows인지?
8. 클라우드 서버인지, 집 공유기 뒤 서버인지, VM인지, Docker인지?
9. 방화벽이나 보안 그룹을 설정했는가?
10. 서비스가 어떤 주소와 포트에 바인딩되어 있는가?
```

우선 요청할 명령어:

Linux 서버:

```bash
ss -tulnp
sudo firewall-cmd --list-all
systemctl status <service>
```

Linux 클라이언트:

```bash
nc -vz <server_ip> <port>
curl -I http://<server_ip>:<port>
```

Windows 클라이언트:

```powershell
Test-NetConnection <server_ip> -Port <port>
```

서버 내부 웹 테스트:

```bash
curl -I http://localhost:<port>
curl -I http://<server_ip>:<port>
```

---

## 에이전트 응답 예시

### 예시 1: ping은 되는데 SSH가 안 되는 경우

사용자 입력:

```text
서버 ping은 되는데 ssh 접속이 안 돼
```

에이전트 응답:

```text
ping이 된다는 것은 서버 IP까지의 기본 도달성은 있다는 뜻입니다. 하지만 SSH는 TCP 22번 포트를 사용하므로, ping 성공이 SSH 접속 성공을 보장하지는 않습니다.

먼저 오류가 `Connection refused`인지 `Connection timed out`인지 확인해야 합니다.

서버에서 아래를 확인하세요.

`systemctl status sshd`
`ss -tulnp | grep ':22'`
`sudo firewall-cmd --list-all`

클라이언트에서는 아래를 실행하세요.

`nc -vz <server_ip> 22`

만약 `Connection refused`라면 sshd가 실행 중이지 않거나 22번 포트에서 listen하지 않는 문제일 가능성이 큽니다. 반면 `timed out`이면 서버 방화벽, 클라우드 보안 그룹, 중간 네트워크 차단 가능성이 더 큽니다.
```

---

### 예시 2: FastAPI 서버가 외부에서 안 열리는 경우

사용자 입력:

```text
uvicorn으로 FastAPI 켰는데 내 컴퓨터에서는 되는데 다른 컴퓨터에서 안 들어와
```

에이전트 응답:

```text
FastAPI/Uvicorn 개발 서버가 외부에서 안 열리는 경우 가장 먼저 바인딩 주소를 확인해야 합니다. `127.0.0.1`로 실행하면 서버 자기 자신에서만 접속 가능하고, 다른 컴퓨터에서는 접속할 수 없습니다.

서버에서 아래 명령어를 확인하세요.

`ss -tulnp | grep ':8000'`

출력이 `127.0.0.1:8000`이면 외부 접속이 안 되는 것이 정상입니다. 다음처럼 실행해야 합니다.

`uvicorn main:app --host 0.0.0.0 --port 8000`

그 다음 서버 방화벽에서 8000번 포트가 열려 있는지 확인하세요.

`sudo firewall-cmd --list-all`

필요하면 다음처럼 허용합니다.

`sudo firewall-cmd --add-port=8000/tcp --permanent`
`sudo firewall-cmd --reload`
```

---

### 예시 3: Connection refused가 발생하는 경우

사용자 입력:

```text
curl 했더니 connection refused가 떠
```

에이전트 응답:

```text
`Connection refused`는 보통 서버에는 도달했지만 해당 포트에서 연결을 받아주는 서비스가 없을 때 발생합니다. 즉, 방화벽이 조용히 막는 timeout과는 다르게, 서버가 연결을 거부했다는 의미에 가깝습니다.

서버에서 먼저 해당 포트가 listen 중인지 확인하세요.

`ss -tulnp | grep ':<port>'`

출력이 없다면 서비스가 실행 중이 아니거나 다른 포트에서 실행 중입니다.

출력이 `127.0.0.1:<port>` 형태라면 외부 접속이 불가능할 수 있으므로, 서비스가 `0.0.0.0` 또는 서버 IP에 바인딩되도록 설정해야 합니다.
```

---

### 예시 4: Connection timed out이 발생하는 경우

사용자 입력:

```text
ssh 접속하면 connection timed out만 나와
```

에이전트 응답:

```text
`Connection timed out`은 클라이언트의 접속 요청에 대해 응답이 돌아오지 않는 상황입니다. 이 경우 서비스 미실행보다는 방화벽, 클라우드 보안 그룹, 네트워크 ACL, NAT/포트포워딩, 라우팅 문제 가능성이 큽니다.

서버에서 SSH가 실행 중인지 먼저 확인하세요.

`systemctl status sshd`
`ss -tulnp | grep ':22'`

서비스가 정상이라면 다음을 확인해야 합니다.

1. 서버 방화벽에서 22/tcp 허용 여부
2. 클라우드 서버라면 보안 그룹 inbound rule
3. 공유기 뒤 서버라면 포트포워딩
4. 서버에 패킷이 도착하는지 tcpdump 확인

서버에서 다음 명령어를 실행한 상태로 클라이언트에서 다시 접속해보세요.

`sudo tcpdump -i <interface> -n port 22`

접속 시도 중에도 SYN 패킷이 보이지 않는다면, 패킷이 서버까지 도달하지 못하고 있는 것입니다.
```

---

### 예시 5: 서버 내부에서는 되는데 외부에서 안 되는 경우

사용자 입력:

```text
서버에서 curl localhost:8000은 되는데 외부에서는 안 돼
```

에이전트 응답:

```text
서버 내부에서 `localhost:8000`이 된다는 것은 애플리케이션 자체는 실행 중일 가능성이 높습니다. 하지만 외부에서 안 된다면 바인딩 주소, 서버 방화벽, 보안 그룹, NAT 문제를 확인해야 합니다.

먼저 서버에서 포트 상태를 확인하세요.

`ss -tulnp | grep ':8000'`

만약 `127.0.0.1:8000`으로 보이면 외부 접속이 안 되는 것이 정상입니다. 이 경우 서비스를 `0.0.0.0:8000`으로 실행해야 합니다.

만약 `0.0.0.0:8000`으로 보이는데 외부 접속이 안 된다면 다음을 확인하세요.

1. 서버 OS 방화벽
2. 클라우드 보안 그룹
3. 공유기 포트포워딩
4. 중간 네트워크 차단
5. tcpdump로 패킷 도착 여부
```

---

### 예시 6: 클라우드 서버에서 포트를 열었는데 안 되는 경우

사용자 입력:

```text
서버에서 방화벽은 열었는데 클라우드 외부 접속이 안 돼
```

에이전트 응답:

```text
클라우드 서버는 OS 내부 방화벽만 열어서는 부족합니다. 클라우드 콘솔의 보안 그룹 또는 네트워크 ACL에서도 인바운드 포트를 허용해야 합니다.

먼저 서버 내부에서 서비스가 listen 중인지 확인하세요.

`ss -tulnp | grep ':<port>'`

그 다음 OS 방화벽을 확인합니다.

`sudo firewall-cmd --list-all`

여기까지 정상이라면 클라우드 콘솔에서 다음을 확인하세요.

1. 인바운드 규칙에 해당 TCP 포트가 있는가
2. Source IP가 내 접속 IP를 허용하는가
3. 보안 그룹이 실제 인스턴스에 연결되어 있는가
4. 서버에 Public IP가 있는가
5. Subnet route table이 인터넷 경로를 가지고 있는가

외부 접속이 timeout이면 보안 그룹이나 네트워크 ACL 차단 가능성이 큽니다.
```

---

## 주의할 점

방화벽/포트 문제를 진단할 때 다음을 주의해야 한다.

1. ping 성공은 특정 포트 접속 가능을 의미하지 않는다.
2. ping 실패도 포트 차단을 의미하지 않는다. ICMP만 차단되었을 수 있다.
3. 방화벽을 무작정 끄기보다 필요한 포트만 열어야 한다.
4. `Connection refused`와 `Connection timed out`은 원인 방향이 다르다.
5. 서버 내부에서 되는지, 같은 LAN에서 되는지, 외부 인터넷에서 되는지를 구분해야 한다.
6. 서비스가 실행 중인지 확인하기 전에 방화벽부터 의심하면 안 된다.
7. `127.0.0.1` 바인딩은 외부 접속이 안 되는 대표 원인이다.
8. 클라우드 서버는 OS 방화벽과 보안 그룹을 둘 다 확인해야 한다.
9. 공유기 뒤 서버는 포트포워딩과 공인 IP 여부를 확인해야 한다.
10. CGNAT 환경에서는 일반 포트포워딩이 동작하지 않을 수 있다.
11. Docker는 컨테이너 내부 포트와 호스트 포트 매핑을 구분해야 한다.
12. VM NAT 모드에서는 외부에서 VM으로 접속하려면 별도 포트포워딩이 필요할 수 있다.
13. UDP 서비스는 TCP 테스트만으로 확인할 수 없다.
14. 포트를 열 때는 프로토콜 TCP/UDP를 정확히 구분해야 한다.
15. 운영 환경에서 SSH를 0.0.0.0/0으로 열면 보안 위험이 크다.
16. MySQL, Redis 같은 DB 포트를 외부 전체에 노출하는 것은 위험하다.
17. 방화벽 규칙 변경 후 reload 또는 서비스 재시작이 필요한 경우가 있다.
18. SELinux가 활성화된 환경에서는 포트와 서비스가 열려 있어도 정책 때문에 막힐 수 있다.
19. 브라우저 접속 실패가 항상 포트 문제는 아니다. DNS, HTTP, TLS, 프록시 문제일 수도 있다.
20. tcpdump로 패킷 도착 여부를 확인하면 서버 이전 문제인지 서버 내부 문제인지 빠르게 구분할 수 있다.

---

## 빠른 진단 요약

```text
1. 서버 IP가 맞는지 확인
2. ping 또는 traceroute로 기본 도달성 확인
3. 클라이언트에서 nc/telnet/Test-NetConnection으로 포트 접속 확인
4. 오류가 refused인지 timeout인지 구분
5. 서버에서 ss -tulnp 또는 netstat으로 리스닝 확인
6. 바인딩 주소가 127.0.0.1인지 0.0.0.0인지 확인
7. 서버 내부에서 localhost 접속 테스트
8. 서버 내부에서 server_ip 접속 테스트
9. 서버 OS 방화벽 확인
10. 클라우드 보안 그룹 또는 네트워크 ACL 확인
11. 공유기/NAT 포트포워딩 확인
12. Docker/VM/WSL 네트워크 모드 확인
13. tcpdump로 서버에 패킷이 도착하는지 확인
14. 서비스 로그와 애플리케이션 설정 확인
```

---

## 핵심 키워드

Firewall, Port Troubleshooting, 방화벽 문제, 포트 문제, 포트 차단, 포트 열기, ping은 되는데 접속 안 됨, SSH 접속 안 됨, HTTP 접속 안 됨, HTTPS 접속 안 됨, MySQL 접속 안 됨, Connection refused, Connection timed out, No route to host, Network is unreachable, Permission denied, TCP 22, TCP 80, TCP 443, TCP 3306, TCP 5432, TCP 6379, FastAPI 8000, Flask 5000, Vite 5173, ss -tulnp, netstat -ano, lsof -i, nc -vz, telnet, Test-NetConnection, curl -I, firewalld, firewall-cmd --list-all, ufw, iptables, nftables, Windows Firewall, Security Group, Network ACL, inbound rule, outbound rule, NAT, port forwarding, 포트포워딩, CGNAT, 이중 NAT, Docker port mapping, docker -p, VM NAT, Bridge, Host-only, WSL, localhost, 127.0.0.1, 0.0.0.0, bind address, listening port, open port, closed port, filtered port, nmap filtered, tcpdump port, SYN, SYN-ACK, RST, SELinux, semanage port, 클라우드 방화벽, 공유기 방화벽, 서버 내부에서는 됨, 외부에서는 안 됨.