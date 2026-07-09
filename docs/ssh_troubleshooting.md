# SSH Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 SSH 접속 실패 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

SSH 문제는 단순히 "접속이 안 된다"로 보이지만 실제 원인은 다양하다. 서버가 꺼져 있을 수도 있고, 네트워크 경로가 막혔을 수도 있으며, SSH 서비스가 실행 중이지 않거나, 22번 포트가 열려 있지 않거나, 방화벽 또는 클라우드 보안 그룹이 차단하고 있을 수도 있다. 또한 포트는 열려 있지만 사용자명, 비밀번호, 공개키, 권한 설정, `sshd_config` 설정 문제로 인증이 실패하는 경우도 많다.

에이전트는 SSH 문제를 진단할 때 다음을 반드시 구분해야 한다.

- 서버 IP까지 네트워크 도달이 가능한지
- SSH 포트까지 TCP 연결이 가능한지
- SSH 서비스가 서버에서 실행 중인지
- SSH가 어느 IP와 포트에 listen 중인지
- 서버 OS 방화벽이 SSH 포트를 허용하는지
- 클라우드 보안 그룹 또는 네트워크 ACL이 SSH를 허용하는지
- 공유기/NAT/포트포워딩이 필요한 환경인지
- 접속 오류가 timeout인지, refused인지, permission denied인지
- 인증 방식이 비밀번호인지, SSH key인지
- 사용자명, 키 파일, 권한, sshd 설정이 맞는지
- 특정 네트워크에서만 안 되는지
- 서버 로그에 어떤 실패 이유가 남는지

SSH 문제는 크게 두 단계로 나눠서 진단한다.

```text
1단계: 네트워크/포트 연결 문제
- 서버에 도달 가능한가?
- 22번 또는 지정한 SSH 포트가 열려 있는가?
- 방화벽/보안 그룹/NAT가 막고 있지 않은가?

2단계: 인증/권한/설정 문제
- 사용자명이 맞는가?
- 비밀번호 로그인이 허용되어 있는가?
- 공개키 인증 설정이 맞는가?
- authorized_keys 권한이 맞는가?
- sshd_config에서 차단하고 있지 않은가?
```

---

## 관련 사용자 표현

사용자는 SSH라는 용어를 정확히 쓰지 않을 수도 있다. 다음 표현은 SSH 문제와 관련될 가능성이 있다.

- SSH 접속이 안 돼
- 서버에 접속이 안 돼
- PuTTY 접속이 안 돼
- PowerShell에서 ssh가 안 돼
- 리눅스 서버에 못 들어가
- 서버 ping은 되는데 ssh가 안 돼
- 22번 포트가 안 열려
- Connection timed out이 떠
- Connection refused가 떠
- Permission denied가 떠
- Permission denied publickey가 떠
- 비밀번호를 맞게 쳤는데 안 돼
- 키 인증이 안 돼
- pem 키로 접속이 안 돼
- private key 권한 문제라고 떠
- host key verification failed가 떠
- remote host identification has changed라고 떠
- no matching host key type이라고 떠
- no route to host가 떠
- network is unreachable이 떠
- connection reset by peer가 떠
- 서버에서 sshd가 안 켜져
- systemctl status sshd가 inactive야
- ssh 포트를 바꿨는데 접속이 안 돼
- root로 ssh 접속이 안 돼
- 특정 사용자만 ssh 접속이 안 돼
- 학교 와이파이에서는 안 되고 핫스팟에서는 돼
- 집에서는 되는데 회사에서는 안 돼
- 같은 LAN에서는 되는데 외부에서는 안 돼
- 외부 IP로 ssh가 안 돼
- 포트포워딩 했는데 ssh가 안 돼
- 클라우드 서버에 ssh 접속이 안 돼
- 보안 그룹 열었는데도 안 돼
- Rocky Linux ssh 접속이 안 돼
- Ubuntu ssh 접속이 안 돼
- OpenWrt ssh 접속이 안 돼
- VirtualBox VM에 ssh 접속이 안 돼
- WSL ssh 접속이 안 돼
- Docker 컨테이너에 ssh 접속이 안 돼
- fail2ban에 막힌 것 같아
- ssh -v 결과를 봐도 모르겠어
- known_hosts 지워야 하나?

---

## 핵심 개념

SSH는 Secure Shell의 약자이며, 원격 서버에 안전하게 접속하기 위한 프로토콜이다. 일반적으로 TCP 22번 포트를 사용한다.

```text
SSH 기본 포트: TCP 22
```

SSH 접속은 보통 다음 흐름으로 진행된다.

```text
Client
  ↓
서버 IP로 TCP 연결 시도
  ↓
서버의 SSH 포트로 접속
  ↓
SSH 프로토콜 협상
  ↓
서버 host key 확인
  ↓
사용자 인증
  ↓
셸 접속 성공
```

이 중 어느 단계에서 실패했는지에 따라 오류 메시지가 달라진다.

```text
서버 IP까지 못 감:
network unreachable, no route to host, timeout

서버에는 도달했지만 포트가 닫힘:
connection refused

포트는 열려 있지만 방화벽이 조용히 버림:
connection timed out

SSH 서비스까지 도달했지만 로그인 실패:
permission denied

서버 host key가 바뀜:
host key verification failed

키 권한이 잘못됨:
bad permissions, unprotected private key file

알고리즘 호환 문제:
no matching host key type, no matching key exchange method
```

따라서 SSH 문제는 오류 메시지를 기준으로 진단 방향을 잡는 것이 중요하다.

---

## SSH 접속 기본 형식

### 기본 접속

```bash
ssh user@server_ip
```

예시:

```bash
ssh minseok@192.168.1.10
```

### 포트를 지정한 접속

SSH 포트가 22번이 아닌 경우 `-p` 옵션을 사용한다.

```bash
ssh -p <port> user@server_ip
```

예시:

```bash
ssh -p 2222 minseok@203.0.113.10
```

주의:

```text
ssh -p 2222 user@server_ip
```

에서 `-p`는 소문자이다.  
`scp`에서는 포트 옵션이 대문자 `-P`이다.

### 개인키를 지정한 접속

```bash
ssh -i <private_key_path> user@server_ip
```

예시:

```bash
ssh -i ~/.ssh/id_rsa minseok@192.168.1.10
ssh -i mykey.pem ubuntu@203.0.113.10
```

### 디버그 모드 접속

```bash
ssh -v user@server_ip
```

더 자세히:

```bash
ssh -vv user@server_ip
ssh -vvv user@server_ip
```

`ssh -v`는 인증 실패, 키 선택, 서버 응답, 알고리즘 협상 문제를 볼 때 매우 중요하다.

---

## SSH 문제의 큰 분류

SSH 문제는 크게 다음 유형으로 나눌 수 있다.

```text
1. 네트워크 도달성 문제
2. 포트 차단 문제
3. SSH 서비스 미실행 문제
4. 바인딩 주소 문제
5. 방화벽 문제
6. 클라우드 보안 그룹 문제
7. NAT/포트포워딩 문제
8. 인증 실패 문제
9. 키 파일 권한 문제
10. sshd_config 설정 문제
11. 계정/권한 문제
12. host key 문제
13. 알고리즘 호환성 문제
14. fail2ban/보안 정책 차단 문제
15. VM/WSL/Docker 네트워크 문제
```

에이전트는 오류 메시지를 보고 어느 유형에 가까운지 먼저 판단해야 한다.

---

## 대표 오류 메시지와 의미

### 1. Connection timed out

예시:

```text
ssh: connect to host 192.168.1.10 port 22: Connection timed out
```

의미:

```text
클라이언트가 서버의 SSH 포트로 TCP 연결을 시도했지만 응답을 받지 못했다.
```

가능한 원인:

- 서버가 꺼져 있음
- 서버 IP가 틀림
- 서버까지 라우팅이 안 됨
- 서버 OS 방화벽이 drop
- 클라우드 보안 그룹이 차단
- 네트워크 ACL이 차단
- 공유기 포트포워딩 누락
- 중간 방화벽에서 TCP 22 차단
- 학교/회사망에서 SSH 차단
- 서버가 사설 IP 뒤에 있음
- CGNAT 환경
- 잘못된 공인 IP로 접속
- SSH 포트가 22가 아닌데 22로 접속

판단:

```text
timeout은 보통 패킷이 중간에서 버려지거나 응답이 돌아오지 않는 상황이다.
서비스 미실행보다는 방화벽, 보안 그룹, NAT, 라우팅 문제 가능성이 크다.
```

우선 확인:

```bash
ping <server_ip>
nc -vz <server_ip> 22
traceroute <server_ip>
```

서버에서 확인 가능하다면:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
```

---

### 2. Connection refused

예시:

```text
ssh: connect to host 192.168.1.10 port 22: Connection refused
```

의미:

```text
서버에는 도달했지만 해당 포트에서 연결을 받아주는 서비스가 없거나, 서버가 연결을 명시적으로 거부했다.
```

가능한 원인:

- sshd 서비스가 실행 중이지 않음
- SSH 서버 패키지가 설치되어 있지 않음
- SSH가 22번이 아닌 다른 포트에서 실행 중
- 22번 포트에 listen 중인 프로세스가 없음
- 방화벽이 reject 방식으로 거부
- SSH가 특정 IP에만 바인딩
- 컨테이너/VM 포트 매핑 누락
- 포트포워딩 대상 내부 포트가 틀림

판단:

```text
Connection refused는 서버 IP까지는 도달했을 가능성이 높다.
따라서 라우팅보다는 sshd 실행 상태, 포트 리스닝, 포트 번호를 먼저 확인한다.
```

서버에서 확인:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo journalctl -u sshd -n 100 --no-pager
```

Ubuntu 계열은 서비스명이 `ssh`일 수 있다.

```bash
systemctl status ssh
journalctl -u ssh -n 100 --no-pager
```

---

### 3. Permission denied

예시:

```text
Permission denied, please try again.
Permission denied (publickey).
Permission denied (publickey,password).
```

의미:

```text
서버의 SSH 서비스까지는 도달했지만 사용자 인증에 실패했다.
```

가능한 원인:

- 사용자명이 틀림
- 비밀번호가 틀림
- 비밀번호 로그인이 비활성화됨
- 공개키 인증만 허용됨
- 개인키가 틀림
- 서버의 `authorized_keys`에 공개키가 없음
- `.ssh` 디렉터리 권한 문제
- `authorized_keys` 파일 권한 문제
- root 로그인이 차단됨
- AllowUsers 또는 DenyUsers 설정
- 계정이 잠김
- 로그인 shell이 비정상
- PAM 설정 문제
- 클라우드 이미지의 기본 사용자명을 잘못 사용

판단:

```text
Permission denied는 네트워크/포트 문제라기보다 인증/계정/키/sshd 설정 문제이다.
```

클라이언트에서 확인:

```bash
ssh -v user@server_ip
ssh -i <keyfile> user@server_ip
```

서버에서 확인:

```bash
sudo journalctl -u sshd -n 100 --no-pager
sudo tail -n 100 /var/log/auth.log
sudo tail -n 100 /var/log/secure
```

배포판별 로그:

```text
Ubuntu/Debian: /var/log/auth.log
RHEL/Rocky/CentOS/Fedora: /var/log/secure 또는 journalctl -u sshd
```

---

### 4. No route to host

예시:

```text
ssh: connect to host 192.168.1.10 port 22: No route to host
```

의미:

```text
클라이언트가 목적지 서버로 갈 경로를 찾지 못했거나, 중간 네트워크에서 도달 불가 응답을 받은 상황이다.
```

가능한 원인:

- 라우팅 테이블 문제
- 기본 게이트웨이 없음
- VPN route 누락
- 목적지 IP가 다른 네트워크에 있음
- 서버가 꺼져 있음
- 방화벽이 ICMP unreachable 반환
- 잘못된 서브넷 마스크
- VM 네트워크 모드 문제

확인:

```bash
ip route
ip route get <server_ip>
ping <server_ip>
traceroute <server_ip>
```

Windows:

```cmd
route print
tracert <server_ip>
```

이 경우 `gateway_routing.md` 문서도 함께 참고해야 한다.

---

### 5. Network is unreachable

예시:

```text
ssh: connect to host 10.10.10.5 port 22: Network is unreachable
```

의미:

```text
클라이언트가 해당 네트워크로 나갈 수 있는 경로를 전혀 가지고 있지 않다.
```

가능한 원인:

- 클라이언트 네트워크 연결 끊김
- IP 주소 없음
- 기본 게이트웨이 없음
- 라우팅 테이블 문제
- VPN 미연결
- 목적지 대역 route 누락
- 인터페이스 down

확인:

```bash
ip addr
ip route
ping <gateway_ip>
```

---

### 6. Could not resolve hostname

예시:

```text
ssh: Could not resolve hostname server.example.com: Name or service not known
```

의미:

```text
SSH가 서버 이름을 IP 주소로 변환하지 못했다.
```

가능한 원인:

- DNS 문제
- 도메인 오타
- 내부 도메인인데 외부 DNS를 사용 중
- VPN 미연결
- `/etc/hosts` 설정 누락
- search domain 문제

확인:

```bash
nslookup server.example.com
dig server.example.com
ping server.example.com
cat /etc/resolv.conf
resolvectl status
```

이 경우 `dns_troubleshooting.md` 문서도 함께 참고해야 한다.

---

### 7. Host key verification failed

예시:

```text
Host key verification failed.
```

의미:

```text
클라이언트가 알고 있는 서버의 host key와 현재 서버가 제시한 host key가 맞지 않는다.
```

가능한 원인:

- 서버 OS 재설치
- 서버 SSH host key 변경
- 같은 IP를 다른 서버가 사용
- 클라우드 인스턴스 재생성
- DNS가 다른 서버를 가리킴
- 중간자 공격 가능성

주의:

이 오류는 보안상 중요한 경고이다. 무조건 known_hosts를 지우면 안 된다. 서버가 실제로 바뀐 것이 맞는지 확인해야 한다.

해결 예시:

```bash
ssh-keygen -R <server_ip>
ssh-keygen -R <hostname>
```

그 다음 다시 접속하면 새로운 host key를 등록할 수 있다.

---

### 8. WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED

예시:

```text
WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!
```

의미:

```text
이전에 접속한 서버의 host key와 현재 서버의 host key가 다르다.
```

가능한 원인:

- 서버 재설치
- IP 재사용
- DNS 변경
- 로드밸런서 뒤 서버 변경
- 클라우드 서버 재생성
- 실제 보안 위협

확인:

```text
서버가 실제로 재설치되었는가?
IP가 다른 서버로 바뀌었는가?
관리자가 host key 변경을 공지했는가?
```

해결:

```bash
ssh-keygen -R <server_ip>
```

---

### 9. UNPROTECTED PRIVATE KEY FILE

예시:

```text
WARNING: UNPROTECTED PRIVATE KEY FILE!
Permissions 0644 for 'mykey.pem' are too open.
This private key will be ignored.
```

의미:

```text
개인키 파일 권한이 너무 열려 있어서 SSH 클라이언트가 보안상 해당 키를 사용하지 않는다.
```

해결:

```bash
chmod 600 <private_key_file>
```

예시:

```bash
chmod 600 mykey.pem
ssh -i mykey.pem ubuntu@server_ip
```

`.ssh` 디렉터리 권한도 중요하다.

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
```

---

### 10. Too many authentication failures

예시:

```text
Too many authentication failures
```

의미:

```text
SSH 클라이언트가 여러 키를 순서대로 시도하다가 서버의 최대 인증 시도 횟수를 초과했다.
```

해결:

특정 키만 사용하도록 지정한다.

```bash
ssh -i <keyfile> -o IdentitiesOnly=yes user@server_ip
```

예시:

```bash
ssh -i mykey.pem -o IdentitiesOnly=yes ubuntu@203.0.113.10
```

---

### 11. No matching host key type / no matching key exchange method

예시:

```text
Unable to negotiate with 192.168.1.10 port 22: no matching host key type found
no matching key exchange method found
```

의미:

```text
클라이언트와 서버가 지원하는 SSH 알고리즘이 맞지 않는다.
```

가능한 원인:

- 오래된 서버
- 오래된 네트워크 장비
- 구형 OpenWrt/임베디드 장비
- 최신 OpenSSH에서 구형 알고리즘 비활성화
- 보안 정책 강화

임시 접속 예시:

```bash
ssh -oHostKeyAlgorithms=+ssh-rsa user@server_ip
```

또는:

```bash
ssh -oKexAlgorithms=+diffie-hellman-group14-sha1 user@server_ip
```

주의:

구형 알고리즘을 허용하는 것은 보안 위험이 있을 수 있다. 운영 환경에서는 서버 SSH 설정을 최신 알고리즘으로 업데이트하는 것이 좋다.

---

## SSH 정상 동작 조건

SSH 접속이 성공하려면 다음 조건이 모두 만족되어야 한다.

```text
1. 클라이언트가 네트워크에 연결되어 있어야 한다.
2. 서버가 켜져 있어야 한다.
3. 클라이언트에서 서버 IP까지 라우팅 가능해야 한다.
4. 서버에서 SSH 서비스가 실행 중이어야 한다.
5. SSH 서비스가 올바른 포트에서 listen 중이어야 한다.
6. 서버 방화벽이 해당 포트를 허용해야 한다.
7. 클라우드 보안 그룹 또는 네트워크 ACL이 해당 포트를 허용해야 한다.
8. NAT/포트포워딩 환경이면 외부 포트가 내부 SSH 포트로 전달되어야 한다.
9. 클라이언트가 올바른 IP, 포트, 사용자명으로 접속해야 한다.
10. 인증 방식이 서버 설정과 맞아야 한다.
11. 키 인증이면 공개키와 개인키 쌍이 맞아야 한다.
12. 계정이 로그인 가능한 상태여야 한다.
```

---

## SSH 서버 서비스 이름

Linux 배포판에 따라 SSH 서비스 이름이 다를 수 있다.

### RHEL / Rocky / CentOS / Fedora 계열

```bash
systemctl status sshd
sudo systemctl start sshd
sudo systemctl enable sshd
```

로그:

```bash
journalctl -u sshd -n 100 --no-pager
```

### Ubuntu / Debian 계열

서비스 이름이 `ssh`인 경우가 많다.

```bash
systemctl status ssh
sudo systemctl start ssh
sudo systemctl enable ssh
```

하지만 프로세스 이름은 `sshd`일 수 있다.

```bash
ps aux | grep sshd
```

로그:

```bash
journalctl -u ssh -n 100 --no-pager
tail -n 100 /var/log/auth.log
```

### OpenWrt

OpenWrt에서는 보통 `dropbear`가 SSH 서버 역할을 한다.

```sh
/etc/init.d/dropbear status
/etc/init.d/dropbear restart
```

포트 확인:

```sh
netstat -tulnp | grep ':22'
```

또는:

```sh
ss -tulnp | grep ':22'
```

---

## sshd_config 핵심 설정

SSH 서버 설정 파일은 보통 다음 위치에 있다.

```text
/etc/ssh/sshd_config
```

설정 변경 후에는 문법 검사를 먼저 하는 것이 좋다.

```bash
sudo sshd -t
```

문제가 없다면 서비스를 재시작한다.

```bash
sudo systemctl restart sshd
```

Ubuntu 계열:

```bash
sudo systemctl restart ssh
```

주의:

원격 SSH로 접속 중인 상태에서 설정을 잘못 바꾸면 재접속이 불가능해질 수 있다. 가능하면 현재 접속 세션을 유지한 채 새 터미널로 재접속 테스트를 해야 한다.

---

### Port

SSH 포트를 지정한다.

```text
Port 22
```

포트를 바꾸면 접속 시 `-p` 옵션이 필요하다.

```bash
ssh -p 2222 user@server_ip
```

포트를 바꾸면 방화벽과 보안 그룹도 함께 변경해야 한다.

---

### ListenAddress

SSH가 listen할 주소를 지정한다.

```text
ListenAddress 0.0.0.0
```

또는 특정 IP만 지정할 수 있다.

```text
ListenAddress 192.168.1.10
```

주의:

`ListenAddress 127.0.0.1`로 되어 있으면 외부에서 SSH 접속이 불가능하다.

---

### PermitRootLogin

root 계정 SSH 로그인을 허용할지 결정한다.

```text
PermitRootLogin no
PermitRootLogin yes
PermitRootLogin prohibit-password
```

보안상 root 직접 로그인은 비활성화하는 것이 일반적이다.

root 접속이 안 되는 경우 이 설정을 확인해야 한다.

---

### PasswordAuthentication

비밀번호 로그인을 허용할지 결정한다.

```text
PasswordAuthentication yes
PasswordAuthentication no
```

`no`이면 비밀번호로는 접속할 수 없고 SSH key 인증을 사용해야 한다.

---

### PubkeyAuthentication

공개키 인증을 허용할지 결정한다.

```text
PubkeyAuthentication yes
```

---

### AuthorizedKeysFile

사용자의 공개키 파일 위치를 지정한다.

```text
AuthorizedKeysFile .ssh/authorized_keys
```

일반적으로 사용자의 홈 디렉터리 아래에 있다.

```text
/home/user/.ssh/authorized_keys
```

---

### AllowUsers / DenyUsers

특정 사용자만 SSH 접속을 허용하거나 차단할 수 있다.

```text
AllowUsers minseok admin
DenyUsers test guest
```

사용자명과 IP 조건을 결합할 수도 있다.

```text
AllowUsers minseok@192.168.1.*
```

---

### MaxAuthTries

인증 시도 횟수를 제한한다.

```text
MaxAuthTries 6
```

키가 너무 많이 시도되어 `Too many authentication failures`가 발생할 수 있다.

---

## SSH 문제의 대표 증상

### 1. SSH 접속 시간이 초과됨

증상:

```text
Connection timed out
```

가능한 원인:

```text
서버 IP 오류
서버 전원 꺼짐
서버 네트워크 단절
서버 방화벽 drop
클라우드 보안 그룹 차단
네트워크 ACL 차단
공유기 포트포워딩 누락
중간 방화벽 차단
학교/회사망에서 SSH 차단
라우팅 문제
```

진단 순서:

```text
1. 서버 IP가 맞는지 확인
2. ping <server_ip>
3. nc -vz <server_ip> 22
4. traceroute <server_ip>
5. 서버에서 sshd 상태 확인
6. 방화벽/보안 그룹 확인
7. tcpdump로 SYN 도착 여부 확인
```

---

### 2. Connection refused 발생

가능한 원인:

```text
sshd 서비스 미실행
SSH 서버 미설치
22번 포트 미리스닝
SSH 포트 변경
방화벽 reject
잘못된 포트포워딩
컨테이너/VM 포트 미연결
```

진단:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
journalctl -u sshd -n 100 --no-pager
```

---

### 3. 서버 IP로 ping은 되지만 SSH 접속이 안 됨

중요한 증상이다.

판단:

```text
ping은 ICMP 도달성만 확인한다.
SSH는 TCP 22 또는 지정된 포트를 사용한다.
따라서 ping 성공이 SSH 포트 성공을 의미하지 않는다.
```

가능한 원인:

```text
SSH 서비스 미실행
22번 포트 미리스닝
서버 방화벽 차단
클라우드 보안 그룹 차단
SSH 포트 변경
접속 IP 제한
fail2ban 차단
```

확인:

```bash
nc -vz <server_ip> 22
ssh -v user@server_ip
```

서버에서:

```bash
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
sudo journalctl -u sshd -n 100 --no-pager
```

---

### 4. 특정 네트워크에서만 SSH 접속 실패

예시:

```text
집에서는 SSH 접속됨
학교 Wi-Fi에서는 안 됨
회사망에서는 안 됨
모바일 핫스팟에서는 됨
```

가능한 원인:

```text
학교/회사 방화벽이 TCP 22 차단
네트워크 정책상 SSH 차단
특정 IP만 서버 방화벽에서 허용
클라우드 보안 그룹 source IP 제한
VPN 필요
DNS가 네트워크마다 다르게 해석됨
프록시 환경
```

판단:

```text
네트워크 위치에 따라 접속 성공 여부가 달라지면 서버 자체 문제보다 중간 네트워크 정책 또는 source IP 제한 문제 가능성이 높다.
```

확인:

```bash
nc -vz <server_ip> 22
ssh -v user@server_ip
```

다른 네트워크와 비교:

```text
집 네트워크
모바일 핫스팟
학교/회사 네트워크
VPN 연결 후
```

---

### 5. 서버 내부에서는 SSH 포트가 열려 있는데 외부 접속 실패

가능한 원인:

```text
서버 OS 방화벽 차단
클라우드 보안 그룹 차단
NAT/포트포워딩 누락
공인 IP 없음
CGNAT
서버가 사설망에만 존재
중간 방화벽 차단
```

서버에서 확인:

```bash
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
```

클라이언트에서 확인:

```bash
nc -vz <server_ip> 22
```

서버에서 패킷 캡처:

```bash
sudo tcpdump -i <interface> -n port 22
```

판단:

```text
외부 접속 시도 중 서버 tcpdump에 SYN이 안 보임:
서버 이전 구간에서 차단. 보안 그룹, NAT, ACL, 중간 방화벽 문제 가능성.

SYN이 보이는데 응답이 없음:
서버 방화벽 drop 또는 정책 문제 가능성.

SYN이 보이고 RST가 나감:
sshd가 해당 포트에서 listen하지 않거나 reject 중.
```

---

### 6. 비밀번호를 맞게 입력해도 로그인 실패

가능한 원인:

```text
사용자명 오류
PasswordAuthentication no
계정 잠김
PAM 정책
root 로그인 차단
키 인증만 허용
비밀번호 만료
키보드 레이아웃 문제
AllowUsers 설정
```

확인:

```bash
sudo grep -E 'PasswordAuthentication|PermitRootLogin|AllowUsers|DenyUsers' /etc/ssh/sshd_config
sudo journalctl -u sshd -n 100 --no-pager
```

계정 상태 확인:

```bash
passwd -S <username>
```

---

### 7. 공개키 인증이 실패함

가능한 원인:

```text
잘못된 개인키 사용
서버 authorized_keys에 공개키 없음
authorized_keys 권한 문제
.ssh 디렉터리 권한 문제
사용자 홈 디렉터리 권한 문제
PubkeyAuthentication no
AuthorizedKeysFile 경로 변경
SELinux context 문제
클라이언트가 다른 키를 먼저 시도
```

서버 권한 권장값:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 755 ~
```

개인키 권한:

```bash
chmod 600 ~/.ssh/id_rsa
chmod 600 mykey.pem
```

클라이언트에서 특정 키 지정:

```bash
ssh -i <keyfile> -o IdentitiesOnly=yes user@server_ip
```

디버그:

```bash
ssh -v -i <keyfile> user@server_ip
```

---

## Possible Causes

SSH 문제의 원인은 크게 네트워크 측, 서버 서비스 측, 방화벽/보안 정책 측, 인증/권한 측, 가상화/NAT 환경 측으로 나눌 수 있다.

---

### 1. 서버가 꺼져 있거나 네트워크에 연결되어 있지 않음

가장 기본적인 원인이다.

확인:

```bash
ping <server_ip>
```

하지만 ping이 실패한다고 서버가 반드시 꺼진 것은 아니다. 서버 또는 방화벽이 ICMP를 차단할 수 있다.

더 정확한 확인:

```bash
nc -vz <server_ip> 22
traceroute <server_ip>
```

서버 콘솔 접근이 가능하다면:

```bash
ip addr
ip route
systemctl status sshd
```

---

### 2. SSH 서비스가 실행 중이지 않음

SSH 서버가 설치되어 있어도 서비스가 꺼져 있으면 접속할 수 없다.

RHEL/Rocky 계열:

```bash
systemctl status sshd
sudo systemctl start sshd
sudo systemctl enable sshd
```

Ubuntu/Debian 계열:

```bash
systemctl status ssh
sudo systemctl start ssh
sudo systemctl enable ssh
```

서비스가 없는 경우 패키지 설치가 필요할 수 있다.

Ubuntu/Debian:

```bash
sudo apt install openssh-server
```

RHEL/Rocky 계열:

```bash
sudo dnf install openssh-server
```

---

### 3. 서버가 22번 포트를 열고 있지 않음

서비스가 실행 중이어도 22번 포트에서 listen하지 않을 수 있다.

확인:

```bash
ss -tulnp | grep ':22'
```

전체 확인:

```bash
ss -tulnp
```

출력 예:

```text
LISTEN 0 128 0.0.0.0:22
LISTEN 0 128 [::]:22
```

정상 의미:

```text
0.0.0.0:22 -> 모든 IPv4 인터페이스에서 SSH 접속 허용
[::]:22 -> IPv6에서 SSH 접속 허용
```

문제 예:

```text
127.0.0.1:22
```

의미:

```text
서버 자기 자신에서만 접속 가능하고 외부에서는 접속 불가.
```

SSH 포트가 변경되었는지 확인:

```bash
grep -E '^Port ' /etc/ssh/sshd_config
```

---

### 4. 서버 방화벽이 SSH 포트를 차단

서버 OS 방화벽이 TCP 22를 차단하면 SSH 접속이 실패한다.

firewalld 확인:

```bash
sudo firewall-cmd --list-all
```

SSH 허용:

```bash
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload
```

포트가 2222처럼 변경된 경우:

```bash
sudo firewall-cmd --add-port=2222/tcp --permanent
sudo firewall-cmd --reload
```

ufw 확인:

```bash
sudo ufw status verbose
```

SSH 허용:

```bash
sudo ufw allow ssh
```

또는:

```bash
sudo ufw allow 22/tcp
```

포트 변경 시:

```bash
sudo ufw allow 2222/tcp
```

주의:

원격 접속 중 방화벽을 수정할 때는 현재 SSH 연결이 끊기지 않도록 조심해야 한다. 새 포트를 열기 전에 기존 SSH 세션을 유지하고, 새 터미널에서 접속 테스트를 해야 한다.

---

### 5. 클라우드 보안 그룹 또는 네트워크 ACL이 차단

클라우드 서버에서는 OS 방화벽 외에도 클라우드 보안 그룹이 SSH를 차단할 수 있다.

확인할 항목:

```text
Inbound Rule에 TCP 22가 허용되어 있는가?
Source IP가 내 공인 IP를 허용하는가?
서버에 해당 보안 그룹이 연결되어 있는가?
Network ACL이 TCP 22를 차단하지 않는가?
서버가 public subnet에 있는가?
Public IP가 연결되어 있는가?
Route table에 인터넷 게이트웨이 경로가 있는가?
```

권장 설정:

```text
TCP 22 Source: 내 공인 IP/32
```

주의:

```text
TCP 22 Source: 0.0.0.0/0
```

은 모든 인터넷에서 SSH 접속을 허용하므로 보안 위험이 크다.

---

### 6. 클라이언트가 잘못된 IP 또는 포트로 접속

자주 발생하는 단순 원인이다.

확인할 것:

```text
서버 IP가 맞는가?
사설 IP와 공인 IP를 혼동하지 않았는가?
SSH 포트가 22가 맞는가?
포트포워딩 외부 포트와 내부 포트를 혼동하지 않았는가?
DNS 이름이 올바른 IP를 가리키는가?
```

포트가 2222라면:

```bash
ssh -p 2222 user@server_ip
```

DNS 확인:

```bash
nslookup <hostname>
dig <hostname>
```

---

### 7. NAT 또는 포트포워딩 문제

집이나 사무실 공유기 뒤의 서버에 외부에서 SSH 접속하려면 포트포워딩이 필요하다.

예시:

```text
공유기 공인 IP: 203.0.113.10
내부 서버 IP: 192.168.0.50
내부 SSH 포트: 22
외부 SSH 포트: 2222
```

포트포워딩:

```text
203.0.113.10:2222 -> 192.168.0.50:22
```

접속:

```bash
ssh -p 2222 user@203.0.113.10
```

확인할 것:

```text
내부 서버 IP가 고정되어 있는가?
포트포워딩 대상 IP가 맞는가?
외부 포트와 내부 포트가 맞는가?
TCP로 설정했는가?
서버 방화벽이 22를 허용하는가?
공유기 WAN IP가 실제 공인 IP인가?
CGNAT이 아닌가?
```

CGNAT 가능성:

```text
공유기 WAN IP가 100.64.x.x
공유기 WAN IP가 10.x.x.x
공유기 WAN IP가 172.16~31.x.x
공유기 WAN IP가 192.168.x.x
공유기 WAN IP와 외부에서 보이는 공인 IP가 다름
```

CGNAT 환경에서는 일반적인 포트포워딩으로 외부 SSH 접속이 어려울 수 있다.

대안:

```text
공인 IP 신청
VPN 사용
Tailscale/ZeroTier 사용
Reverse SSH Tunnel 사용
Cloudflare Tunnel 사용
클라우드 서버를 중계 서버로 사용
```

---

### 8. 사용자명 오류

SSH 접속에서는 사용자명이 중요하다.

예시:

```bash
ssh root@server_ip
ssh ubuntu@server_ip
ssh ec2-user@server_ip
ssh rocky@server_ip
ssh admin@server_ip
```

클라우드 이미지 기본 사용자명은 배포판마다 다를 수 있다.

예시:

```text
Ubuntu: ubuntu
Amazon Linux: ec2-user
Rocky Linux: rocky 또는 설정된 사용자
CentOS: centos
Debian: debian
OpenWrt: root
```

사용자명이 틀리면 비밀번호나 키가 맞아도 인증이 실패한다.

---

### 9. root 로그인 차단

많은 Linux 서버는 보안상 root SSH 로그인을 막는다.

확인:

```bash
grep -E '^PermitRootLogin' /etc/ssh/sshd_config
```

설정 예:

```text
PermitRootLogin no
PermitRootLogin prohibit-password
```

이 경우 일반 사용자로 접속한 뒤 `sudo`를 사용해야 한다.

```bash
ssh user@server_ip
sudo -i
```

---

### 10. 비밀번호 로그인 비활성화

서버에서 비밀번호 로그인을 막고 공개키 인증만 허용할 수 있다.

확인:

```bash
grep -E '^PasswordAuthentication' /etc/ssh/sshd_config
```

설정:

```text
PasswordAuthentication no
```

이 경우 비밀번호를 입력해도 접속할 수 없으며, 올바른 개인키를 사용해야 한다.

---

### 11. SSH Key 권한 문제

SSH key 인증에서는 파일 권한이 매우 중요하다.

클라이언트 개인키 권한:

```bash
chmod 600 ~/.ssh/id_rsa
chmod 600 mykey.pem
```

서버 사용자 홈 디렉터리 권한:

```bash
chmod 755 ~
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

권한이 너무 열려 있으면 SSH 서버가 `authorized_keys`를 무시할 수 있다.

---

### 12. SELinux 문제

RHEL/Rocky 계열에서는 SELinux가 SSH 동작에 영향을 줄 수 있다.

확인:

```bash
getenforce
sestatus
```

SSH 포트를 22가 아닌 다른 포트로 바꾼 경우 SELinux port context가 필요할 수 있다.

예시: SSH를 2222 포트로 변경한 경우

```bash
sudo semanage port -a -t ssh_port_t -p tcp 2222
```

이미 등록된 경우:

```bash
sudo semanage port -m -t ssh_port_t -p tcp 2222
```

확인:

```bash
sudo semanage port -l | grep ssh
```

주의:

SELinux를 무조건 끄는 것은 권장되지 않는다. 필요한 port context를 추가하는 방식이 좋다.

---

### 13. fail2ban 또는 보안 정책 차단

로그인 실패가 반복되면 fail2ban 같은 도구가 클라이언트 IP를 차단할 수 있다.

증상:

```text
처음에는 접속되다가 갑자기 timeout 또는 refused
특정 IP에서만 접속 안 됨
다른 네트워크에서는 접속됨
```

확인:

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
```

차단 해제 예시:

```bash
sudo fail2ban-client set sshd unbanip <client_ip>
```

로그 확인:

```bash
sudo journalctl -u fail2ban --no-pager
```

---

### 14. VM 네트워크 문제

VirtualBox, VMware, Hyper-V VM에 SSH 접속할 때는 VM 네트워크 모드가 중요하다.

### NAT 모드

VM이 외부로 나가는 것은 가능하지만, 호스트나 외부에서 VM으로 접속하려면 포트포워딩이 필요할 수 있다.

예시:

```text
Host port 2222 -> Guest port 22
```

접속:

```bash
ssh -p 2222 user@127.0.0.1
```

또는 호스트 IP 사용.

### Bridge 모드

VM이 실제 LAN에 직접 연결된 장비처럼 IP를 받는다.

접속:

```bash
ssh user@<vm_lan_ip>
```

확인:

```bash
ip addr
ip route
systemctl status sshd
```

### Host-only 모드

호스트와 VM 사이의 내부망이다. 외부 인터넷에서는 직접 접속할 수 없을 수 있다.

접속은 보통 호스트에서 VM의 host-only IP로 한다.

---

### 15. WSL SSH 문제

WSL 내부에서 SSH 서버를 실행하는 경우 일반 Linux 서버와 다르게 Windows NAT/포트 전달 구조를 고려해야 한다.

가능한 문제:

```text
WSL IP가 재시작마다 바뀜
Windows 방화벽 차단
WSL 내부 sshd 미실행
Windows에서 WSL로 포트프록시 필요
localhost forwarding 설정 문제
```

확인:

WSL 내부:

```bash
ip addr
systemctl status ssh
ss -tulnp | grep ':22'
```

Windows PowerShell:

```powershell
Test-NetConnection 127.0.0.1 -Port 22
```

---

### 16. Docker 컨테이너 SSH 문제

일반적으로 Docker 컨테이너에 SSH로 접속하는 방식은 권장되지 않는다. 컨테이너 관리는 보통 `docker exec`를 사용한다.

```bash
docker exec -it <container_name> bash
```

그래도 SSH 서버를 컨테이너 안에서 운영한다면 다음을 확인해야 한다.

```text
컨테이너 내부 sshd 실행 여부
컨테이너 포트 22 listen 여부
docker -p 포트 매핑 여부
호스트 방화벽
컨테이너 내부 사용자/비밀번호/키 설정
```

포트 매핑 예:

```bash
docker run -p 2222:22 my-ssh-container
```

접속:

```bash
ssh -p 2222 user@localhost
```

---

## Recommended Commands

SSH 문제는 클라이언트와 서버 양쪽에서 확인해야 한다.

---

## 클라이언트 측 진단 명령어

### 서버 IP 도달성 확인

```bash
ping <server_ip>
```

주의:

ping 실패가 반드시 SSH 실패를 의미하지는 않는다. ICMP가 차단되어도 SSH는 될 수 있다.

### SSH 포트 접속 확인

```bash
nc -vz <server_ip> 22
```

포트가 다르면:

```bash
nc -vz <server_ip> <port>
```

### telnet으로 포트 확인

```bash
telnet <server_ip> 22
```

### SSH 디버그 모드

```bash
ssh -v user@server_ip
```

더 자세히:

```bash
ssh -vv user@server_ip
ssh -vvv user@server_ip
```

### 특정 포트 접속

```bash
ssh -p <port> user@server_ip
```

### 특정 키 접속

```bash
ssh -i <private_key> user@server_ip
```

### 특정 키만 사용

```bash
ssh -i <private_key> -o IdentitiesOnly=yes user@server_ip
```

### 경로 확인

Linux:

```bash
traceroute <server_ip>
```

Windows:

```cmd
tracert <server_ip>
```

### DNS 이름 확인

```bash
nslookup <hostname>
dig <hostname>
```

---

## Windows 클라이언트 진단 명령어

### PowerShell SSH 접속

```powershell
ssh user@server_ip
```

포트 지정:

```powershell
ssh -p 2222 user@server_ip
```

키 지정:

```powershell
ssh -i .\key.pem user@server_ip
```

### 포트 테스트

```powershell
Test-NetConnection <server_ip> -Port 22
```

예시:

```powershell
Test-NetConnection 192.168.1.10 -Port 22
```

확인할 항목:

```text
TcpTestSucceeded
RemoteAddress
RemotePort
InterfaceAlias
SourceAddress
PingSucceeded
```

### 라우팅 확인

```cmd
route print
```

### DNS 확인

```cmd
nslookup <hostname>
```

### PuTTY 사용 시 확인할 것

```text
Host Name에 IP 또는 도메인을 정확히 입력했는가?
Port가 22 또는 변경된 포트인가?
Connection type이 SSH인가?
키 인증이면 .ppk 파일을 올바르게 지정했는가?
사용자명이 맞는가?
```

PuTTY는 OpenSSH의 PEM 키가 아니라 PPK 형식을 요구하는 경우가 있다. 이 경우 PuTTYgen으로 변환해야 할 수 있다.

---

## 서버 측 진단 명령어

### SSH 서비스 상태 확인

RHEL/Rocky 계열:

```bash
systemctl status sshd
```

Ubuntu/Debian 계열:

```bash
systemctl status ssh
```

### SSH 서비스 시작

```bash
sudo systemctl start sshd
```

Ubuntu/Debian:

```bash
sudo systemctl start ssh
```

### 부팅 시 자동 시작

```bash
sudo systemctl enable sshd
```

Ubuntu/Debian:

```bash
sudo systemctl enable ssh
```

### SSH 포트 listen 확인

```bash
ss -tulnp | grep ':22'
```

전체 확인:

```bash
ss -tulnp
```

### 프로세스 확인

```bash
ps aux | grep sshd
```

### SSH 설정 문법 검사

```bash
sudo sshd -t
```

### SSH 설정 확인

```bash
sudo grep -E '^(Port|ListenAddress|PermitRootLogin|PasswordAuthentication|PubkeyAuthentication|AllowUsers|DenyUsers|AuthorizedKeysFile)' /etc/ssh/sshd_config
```

### SSH 로그 확인

RHEL/Rocky 계열:

```bash
sudo journalctl -u sshd -n 100 --no-pager
sudo tail -n 100 /var/log/secure
```

Ubuntu/Debian 계열:

```bash
sudo journalctl -u ssh -n 100 --no-pager
sudo tail -n 100 /var/log/auth.log
```

---

## 방화벽 확인 명령어

### firewalld

```bash
sudo firewall-cmd --list-all
```

SSH 허용:

```bash
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload
```

포트 변경 시:

```bash
sudo firewall-cmd --add-port=2222/tcp --permanent
sudo firewall-cmd --reload
```

### ufw

```bash
sudo ufw status verbose
```

SSH 허용:

```bash
sudo ufw allow ssh
```

또는:

```bash
sudo ufw allow 22/tcp
```

포트 변경 시:

```bash
sudo ufw allow 2222/tcp
```

### iptables

```bash
sudo iptables -L -n -v
```

### nftables

```bash
sudo nft list ruleset
```

---

## OpenWrt SSH 진단 명령어

OpenWrt는 보통 Dropbear SSH 서버를 사용한다.

### Dropbear 상태 확인

```sh
/etc/init.d/dropbear status
```

### Dropbear 재시작

```sh
/etc/init.d/dropbear restart
```

### 포트 확인

```sh
netstat -tulnp | grep ':22'
```

또는:

```sh
ss -tulnp | grep ':22'
```

### 설정 확인

```sh
uci show dropbear
```

### 로그 확인

```sh
logread | grep dropbear
```

### 방화벽 확인

```sh
uci show firewall
```

주의:

OpenWrt에서 WAN 쪽 SSH 접속은 기본적으로 막혀 있는 경우가 많다. 보안상 WAN에서 라우터 SSH를 여는 것은 위험하므로, 가능하면 LAN 또는 VPN을 통해 접속하는 것이 좋다.

---

## Packet Capture로 SSH 확인

명령어 출력만으로 원인을 찾기 어려우면 서버에서 tcpdump로 SSH 패킷이 도착하는지 확인한다.

### 서버에서 22번 포트 패킷 확인

```bash
sudo tcpdump -i <interface> -n port 22
```

포트가 다르면:

```bash
sudo tcpdump -i <interface> -n port <ssh_port>
```

### 특정 클라이언트만 확인

```bash
sudo tcpdump -i <interface> -n host <client_ip> and port 22
```

### 판단 기준

```text
클라이언트가 접속 시도하는데 서버 tcpdump에 SYN이 보이지 않음:
서버까지 패킷이 도달하지 못함. 클라우드 보안 그룹, 네트워크 ACL, NAT, 포트포워딩, 중간 방화벽 문제 가능성.

SYN이 보이고 SYN-ACK가 나감:
서버는 응답하고 있음. 클라이언트 방향 return path, 중간 방화벽, 클라이언트 방화벽 문제 가능성.

SYN이 보이고 RST가 나감:
해당 포트에서 서비스가 listen하지 않거나 connection refused 상황.

SYN은 보이지만 응답이 없음:
서버 방화벽 drop 또는 커널/보안 정책 문제 가능성.

TCP 연결 후 SSH banner가 오감:
네트워크/포트는 정상이고 인증/알고리즘/계정 문제 가능성이 높음.
```

---

## 단계별 진단 절차

SSH 문제는 다음 순서로 진단하는 것이 좋다.

---

### 1단계: 접속 정보 확인

확인할 것:

```text
서버 IP가 맞는가?
도메인 이름이 맞는가?
포트 번호가 맞는가?
사용자명이 맞는가?
비밀번호 인증인지 키 인증인지?
서버가 클라우드인지, VM인지, 공유기 뒤인지?
```

기본 접속:

```bash
ssh user@server_ip
```

포트 지정:

```bash
ssh -p <port> user@server_ip
```

키 지정:

```bash
ssh -i <keyfile> user@server_ip
```

---

### 2단계: 네트워크 도달성 확인

```bash
ping <server_ip>
```

판단:

```text
ping 성공:
서버 IP까지 ICMP 도달성은 있음. SSH 포트 문제로 좁힐 수 있음.

ping 실패:
서버가 꺼졌거나 ICMP 차단, 라우팅 문제, 네트워크 단절 가능성.
```

라우팅 확인:

```bash
traceroute <server_ip>
```

Windows:

```cmd
tracert <server_ip>
```

---

### 3단계: SSH 포트 접속 확인

```bash
nc -vz <server_ip> 22
```

Windows:

```powershell
Test-NetConnection <server_ip> -Port 22
```

판단:

```text
succeeded:
포트 연결 가능. 인증/계정/키 문제 가능성.

connection refused:
서버 도달 가능하지만 sshd 미실행 또는 포트 미리스닝 가능성.

timed out:
방화벽, 보안 그룹, NAT, 라우팅 문제 가능성.

no route to host:
라우팅 문제 가능성.
```

---

### 4단계: 서버에서 sshd 상태 확인

RHEL/Rocky:

```bash
systemctl status sshd
```

Ubuntu/Debian:

```bash
systemctl status ssh
```

실행 중이 아니면 시작:

```bash
sudo systemctl start sshd
```

Ubuntu/Debian:

```bash
sudo systemctl start ssh
```

---

### 5단계: 서버에서 포트 리스닝 확인

```bash
ss -tulnp | grep ':22'
```

판단:

```text
0.0.0.0:22:
모든 IPv4 인터페이스에서 접속 가능.

127.0.0.1:22:
로컬에서만 접속 가능. 외부 접속 불가.

출력 없음:
sshd가 22번에서 listen하지 않음. 서비스 미실행 또는 포트 변경 가능성.

다른 포트에서 sshd가 보임:
클라이언트가 해당 포트로 접속해야 함.
```

---

### 6단계: 방화벽 확인

firewalld:

```bash
sudo firewall-cmd --list-all
```

ufw:

```bash
sudo ufw status verbose
```

SSH 허용:

```bash
sudo firewall-cmd --add-service=ssh --permanent
sudo firewall-cmd --reload
```

또는:

```bash
sudo ufw allow ssh
```

---

### 7단계: 클라우드 보안 그룹 또는 NAT 확인

클라우드 서버라면:

```text
보안 그룹 inbound TCP 22 확인
Source IP 확인
public IP 확인
subnet route table 확인
network ACL 확인
```

공유기 뒤 서버라면:

```text
포트포워딩 확인
공유기 WAN IP 확인
CGNAT 여부 확인
서버 사설 IP 고정 확인
```

---

### 8단계: SSH 디버그로 인증 문제 확인

```bash
ssh -v user@server_ip
```

키 인증:

```bash
ssh -v -i <keyfile> user@server_ip
```

확인할 로그:

```text
Offering public key
Server accepts key
Authentications that can continue
Permission denied
Too many authentication failures
No more authentication methods to try
```

---

### 9단계: 서버 로그 확인

RHEL/Rocky:

```bash
sudo journalctl -u sshd -n 100 --no-pager
sudo tail -n 100 /var/log/secure
```

Ubuntu/Debian:

```bash
sudo journalctl -u ssh -n 100 --no-pager
sudo tail -n 100 /var/log/auth.log
```

로그에서 확인할 내용:

```text
Failed password
Invalid user
Accepted password
Accepted publickey
Authentication refused
User not allowed
Connection closed
Disconnected from
PAM
```

---

### 10단계: 계정과 키 권한 확인

서버에서:

```bash
ls -ld ~
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys
```

권한 설정:

```bash
chmod 755 ~
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

클라이언트 개인키:

```bash
chmod 600 <private_key>
```

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
ping 실패 + SSH timeout:
서버 전원, 네트워크 연결, 라우팅, 방화벽, 보안 그룹 문제 가능성이 있다.

ping 성공 + SSH timeout:
ICMP는 허용되지만 TCP 22가 방화벽, 보안 그룹, ACL, NAT에서 차단될 가능성이 높다.

ping 성공 + Connection refused:
서버는 도달 가능하지만 sshd가 실행 중이지 않거나 해당 포트에서 listen하지 않을 가능성이 높다.

nc -vz 성공 + SSH Permission denied:
네트워크/포트는 정상이고 인증, 사용자명, 비밀번호, 키 문제 가능성이 높다.

ss -tulnp에 22번 포트가 없음:
SSH 서비스 미실행 또는 포트 변경 가능성이 높다.

ss -tulnp에 127.0.0.1:22만 있음:
외부 접속 불가. ListenAddress 설정 문제 가능성이 있다.

ss -tulnp에 0.0.0.0:22 있음 + 외부 timeout:
서버 서비스는 정상. 방화벽, 보안 그룹, NAT, 중간 네트워크 문제 가능성이 높다.

서버 tcpdump에 SYN이 안 보임:
패킷이 서버까지 도달하지 못함. 보안 그룹, NAT, ACL, 라우팅 문제 가능성이 높다.

서버 tcpdump에 SYN이 보이고 RST가 나감:
해당 포트에 SSH 서비스가 없거나 connection refused 상황이다.

Permission denied publickey:
사용자명, 개인키, authorized_keys, 권한, PubkeyAuthentication 설정 문제 가능성이 높다.

비밀번호를 맞게 입력해도 실패:
PasswordAuthentication no, 사용자명 오류, 계정 잠금, PAM, root 로그인 차단 가능성이 있다.

Host key verification failed:
서버 host key가 변경되었거나 IP/DNS가 다른 서버를 가리킬 수 있다.

특정 네트워크에서만 SSH 실패:
중간 네트워크의 TCP 22 차단, source IP 제한, 보안 그룹 source 제한 가능성이 높다.

클라우드 서버에서 OS 방화벽은 열었는데 timeout:
클라우드 보안 그룹 또는 네트워크 ACL을 확인해야 한다.

공유기 뒤 서버에서 LAN SSH는 되지만 외부 SSH 실패:
포트포워딩, 공인 IP, CGNAT, 이중 NAT 문제 가능성이 높다.

SSH 포트를 변경한 뒤 접속 실패:
sshd_config, 방화벽, SELinux, 클라우드 보안 그룹을 모두 새 포트에 맞게 수정해야 한다.
```

---

## 문제 유형별 해결 방법

### SSH 접속 시간이 초과될 때

1. 서버 IP 확인
2. ping 확인
3. `nc -vz <server_ip> 22` 확인
4. traceroute 확인
5. 서버가 켜져 있는지 확인
6. 서버 방화벽 확인
7. 클라우드 보안 그룹 확인
8. NAT/포트포워딩 확인
9. tcpdump로 SYN 도착 여부 확인

명령어:

```bash
ping <server_ip>
nc -vz <server_ip> 22
traceroute <server_ip>
```

서버:

```bash
sudo tcpdump -i <interface> -n port 22
```

---

### Connection refused가 발생할 때

1. SSH 서비스 실행 여부 확인
2. 22번 포트 listen 확인
3. SSH 포트가 변경되었는지 확인
4. sshd_config 문법 확인
5. SSH 서비스 재시작
6. 서버 로그 확인

명령어:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo sshd -t
sudo journalctl -u sshd -n 100 --no-pager
```

Ubuntu/Debian:

```bash
systemctl status ssh
sudo journalctl -u ssh -n 100 --no-pager
```

---

### Permission denied가 발생할 때

1. 사용자명 확인
2. 비밀번호 인증 허용 여부 확인
3. 공개키 인증 여부 확인
4. 올바른 개인키 사용 여부 확인
5. authorized_keys 확인
6. `.ssh` 권한 확인
7. root 로그인 허용 여부 확인
8. AllowUsers/DenyUsers 확인
9. 서버 로그 확인

명령어:

```bash
ssh -v user@server_ip
ssh -i <keyfile> -o IdentitiesOnly=yes user@server_ip
```

서버:

```bash
sudo journalctl -u sshd -n 100 --no-pager
ls -ld ~/.ssh
ls -l ~/.ssh/authorized_keys
```

---

### 공개키 인증이 안 될 때

1. 개인키와 공개키 쌍이 맞는지 확인
2. 서버의 `authorized_keys`에 공개키가 있는지 확인
3. 파일 권한 확인
4. PubkeyAuthentication 설정 확인
5. 클라이언트가 올바른 키를 사용하는지 확인
6. `ssh -v`로 어떤 키를 시도하는지 확인

권한:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chmod 600 <private_key>
```

접속:

```bash
ssh -i <private_key> -o IdentitiesOnly=yes user@server_ip
```

---

### root로 SSH 접속이 안 될 때

1. root 로그인이 허용되어 있는지 확인
2. 비밀번호 로그인이 허용되어 있는지 확인
3. root 비밀번호가 설정되어 있는지 확인
4. 보안 정책상 root 직접 로그인 차단 여부 확인
5. 일반 사용자로 접속 후 sudo 사용

확인:

```bash
grep -E '^PermitRootLogin|^PasswordAuthentication' /etc/ssh/sshd_config
```

권장:

```bash
ssh user@server_ip
sudo -i
```

---

### SSH 포트를 변경했을 때

1. `sshd_config`에서 Port 확인
2. 문법 검사
3. 방화벽에서 새 포트 허용
4. SELinux port context 추가
5. 클라우드 보안 그룹에서 새 포트 허용
6. 클라이언트에서 `-p` 옵션 사용

예시:

```text
Port 2222
```

문법 검사:

```bash
sudo sshd -t
```

방화벽:

```bash
sudo firewall-cmd --add-port=2222/tcp --permanent
sudo firewall-cmd --reload
```

SELinux:

```bash
sudo semanage port -a -t ssh_port_t -p tcp 2222
```

접속:

```bash
ssh -p 2222 user@server_ip
```

---

### 클라우드 서버 SSH가 안 될 때

1. Public IP 확인
2. 사용자명 확인
3. 키 파일 확인
4. 보안 그룹 inbound TCP 22 확인
5. Source IP 확인
6. Network ACL 확인
7. OS 방화벽 확인
8. sshd 상태 확인
9. 서버 콘솔에서 로그 확인

접속 예:

```bash
ssh -i key.pem ubuntu@<public_ip>
```

권한:

```bash
chmod 600 key.pem
```

보안 그룹:

```text
TCP 22
Source: 내 공인 IP/32
```

---

### VM에 SSH 접속이 안 될 때

1. VM 네트워크 모드 확인
2. VM IP 확인
3. NAT 모드면 포트포워딩 확인
4. Bridge 모드면 VM의 LAN IP로 접속
5. VM 내부 sshd 상태 확인
6. VM 내부 방화벽 확인
7. 호스트 방화벽 확인

VM 내부:

```bash
ip addr
ip route
systemctl status sshd
ss -tulnp | grep ':22'
```

VirtualBox NAT 예:

```text
Host Port 2222 -> Guest Port 22
```

접속:

```bash
ssh -p 2222 user@127.0.0.1
```

---

### 공유기 뒤 서버에 외부 SSH가 안 될 때

1. 같은 LAN에서 사설 IP로 SSH 되는지 확인
2. 서버 사설 IP 고정
3. 공유기 포트포워딩 설정 확인
4. 서버 방화벽 확인
5. 공유기 WAN IP와 실제 공인 IP 비교
6. CGNAT 여부 확인
7. 외부 네트워크에서 테스트

LAN 내부:

```bash
ssh user@192.168.0.50
```

외부:

```bash
ssh -p 2222 user@<public_ip>
```

---

## 에이전트 응답 전략

SSH 문제로 의심될 때 에이전트는 바로 "방화벽을 열어라"라고 하면 안 된다. 먼저 오류 메시지를 확인하고, 네트워크/포트 문제인지 인증 문제인지 구분해야 한다.

우선 물어볼 정보:

```text
1. 접속 명령어가 무엇인가?
2. 서버 IP와 포트가 무엇인가?
3. 오류 메시지가 정확히 무엇인가?
4. ping은 되는가?
5. nc 또는 Test-NetConnection으로 22번 포트가 열리는가?
6. 서버 OS는 무엇인가?
7. 서버가 클라우드인지, 집 공유기 뒤인지, VM인지, OpenWrt인지?
8. SSH 서비스가 실행 중인가?
9. ss -tulnp에서 22번 포트가 보이는가?
10. 방화벽 또는 보안 그룹을 설정했는가?
11. 비밀번호 인증인지 키 인증인지?
12. 특정 네트워크에서만 안 되는가?
```

우선 요청할 명령어:

클라이언트:

```bash
ssh -v user@server_ip
ping <server_ip>
nc -vz <server_ip> 22
```

Windows:

```powershell
Test-NetConnection <server_ip> -Port 22
```

서버:

```bash
systemctl status sshd
ss -tulnp | grep ':22'
sudo firewall-cmd --list-all
sudo journalctl -u sshd -n 100 --no-pager
```

Ubuntu/Debian 서버:

```bash
systemctl status ssh
sudo journalctl -u ssh -n 100 --no-pager
```

---

## 에이전트 응답 예시

### 예시 1: ping은 되는데 SSH가 timeout

사용자 입력:

```text
서버 ping은 되는데 ssh 접속하면 timeout 떠
```

에이전트 응답:

```text
ping이 된다는 것은 서버 IP까지 ICMP 도달성은 있다는 뜻입니다. 하지만 SSH는 TCP 22번 포트를 사용하므로, ping 성공이 SSH 접속 가능을 의미하지는 않습니다.

`Connection timed out`이면 SSH 요청이 중간에서 버려지거나 응답이 돌아오지 않는 상황일 가능성이 큽니다. 서버 방화벽, 클라우드 보안 그룹, 네트워크 ACL, 포트포워딩 문제를 확인해야 합니다.

클라이언트에서 먼저 확인하세요.

`nc -vz <server_ip> 22`

Windows라면:

`Test-NetConnection <server_ip> -Port 22`

서버에 콘솔로 접근 가능하다면 다음도 확인하세요.

`systemctl status sshd`
`ss -tulnp | grep ':22'`
`sudo firewall-cmd --list-all`

클라우드 서버라면 보안 그룹 inbound rule에서 TCP 22가 내 IP에 대해 허용되어 있는지도 확인해야 합니다.
```

---

### 예시 2: Connection refused

사용자 입력:

```text
ssh 접속하면 connection refused가 나와
```

에이전트 응답:

```text
`Connection refused`는 보통 서버에는 도달했지만 해당 포트에서 연결을 받아주는 SSH 서비스가 없을 때 발생합니다. 즉, 방화벽이 조용히 막는 timeout과는 다르게 sshd가 실행 중이 아니거나 22번 포트에서 listen하지 않는 상황일 가능성이 큽니다.

서버에서 아래를 확인하세요.

`systemctl status sshd`
`ss -tulnp | grep ':22'`

Ubuntu/Debian 계열이면 서비스명이 `ssh`일 수 있습니다.

`systemctl status ssh`

만약 22번 포트가 보이지 않는다면 sshd가 꺼져 있거나 SSH 포트가 변경되었을 수 있습니다. `/etc/ssh/sshd_config`에서 `Port` 설정을 확인하세요.
```

---

### 예시 3: Permission denied publickey

사용자 입력:

```text
Permission denied (publickey)라고 떠
```

에이전트 응답:

```text
`Permission denied (publickey)`는 네트워크나 포트 문제라기보다는 SSH 서버까지는 도달했지만 공개키 인증에 실패했다는 뜻입니다.

먼저 사용자명과 키 파일이 맞는지 확인하세요.

`ssh -i <keyfile> -o IdentitiesOnly=yes user@server_ip`

디버그를 보려면:

`ssh -v -i <keyfile> user@server_ip`

서버 쪽에서는 해당 사용자의 `~/.ssh/authorized_keys`에 공개키가 들어 있어야 하고, 권한도 중요합니다.

서버 권한 권장값은 다음과 같습니다.

`chmod 700 ~/.ssh`
`chmod 600 ~/.ssh/authorized_keys`

클라이언트 개인키는 다음처럼 설정합니다.

`chmod 600 <keyfile>`

또한 클라우드 서버라면 배포판별 기본 사용자명이 다를 수 있으므로 `ubuntu`, `ec2-user`, `rocky`, `centos` 등을 잘못 쓰고 있지 않은지도 확인해야 합니다.
```

---

### 예시 4: Host key verification failed

사용자 입력:

```text
host key verification failed가 떠
```

에이전트 응답:

```text
`Host key verification failed`는 예전에 접속했던 서버의 host key와 지금 접속하려는 서버의 host key가 다르다는 뜻입니다. 서버를 재설치했거나, 같은 IP를 다른 서버가 사용하게 되었거나, DNS가 다른 서버를 가리키는 경우 발생할 수 있습니다.

보안상 중요한 경고이므로 무조건 지우기 전에 서버가 실제로 바뀐 것이 맞는지 확인해야 합니다.

서버 변경이 확실하다면 기존 known_hosts 항목을 제거할 수 있습니다.

`ssh-keygen -R <server_ip>`

도메인으로 접속했다면:

`ssh-keygen -R <hostname>`

그 다음 다시 접속하면 새로운 host key를 등록할 수 있습니다.
```

---

### 예시 5: 클라우드 서버 SSH가 안 되는 경우

사용자 입력:

```text
클라우드 서버 만들었는데 ssh가 안 돼
```

에이전트 응답:

```text
클라우드 서버 SSH 문제는 OS 내부 설정뿐 아니라 클라우드 보안 그룹을 반드시 함께 확인해야 합니다.

먼저 접속 명령어가 올바른지 확인하세요.

`ssh -i key.pem user@<public_ip>`

개인키 권한도 설정해야 합니다.

`chmod 600 key.pem`

그 다음 클라우드 콘솔에서 다음을 확인하세요.

1. 서버에 Public IP가 있는가
2. Inbound rule에 TCP 22가 허용되어 있는가
3. Source가 내 공인 IP를 허용하는가
4. 해당 보안 그룹이 실제 서버에 연결되어 있는가
5. Subnet route table에 인터넷 경로가 있는가

서버 콘솔 접근이 가능하다면 내부에서 다음도 확인하세요.

`systemctl status sshd`
`ss -tulnp | grep ':22'`
`sudo firewall-cmd --list-all`
```

---

### 예시 6: 외부에서는 안 되고 LAN에서는 되는 경우

사용자 입력:

```text
같은 공유기 안에서는 ssh 되는데 밖에서는 안 돼
```

에이전트 응답:

```text
같은 LAN에서 서버 사설 IP로 SSH가 되는데 외부에서 안 된다면 서버의 sshd 자체는 정상일 가능성이 높습니다. 이 경우 공유기 포트포워딩, 공인 IP, CGNAT, 서버 방화벽을 확인해야 합니다.

확인할 내용은 다음과 같습니다.

1. 서버 내부 IP가 고정되어 있는가
2. 공유기 포트포워딩이 `외부포트 -> 서버IP:22`로 되어 있는가
3. TCP로 설정되어 있는가
4. 공유기 WAN IP와 외부에서 보이는 공인 IP가 같은가
5. 서버 방화벽에서 SSH가 허용되어 있는가

예를 들어 외부 포트 2222를 내부 22번으로 전달했다면 접속은 다음처럼 해야 합니다.

`ssh -p 2222 user@<public_ip>`

만약 공유기 WAN IP가 100.64.x.x, 10.x.x.x, 192.168.x.x 같은 사설 또는 CGNAT 대역이면 일반 포트포워딩으로는 외부 SSH가 어려울 수 있습니다.
```

---

### 예시 7: VM에 SSH 접속이 안 되는 경우

사용자 입력:

```text
VirtualBox 리눅스 VM에 ssh가 안 돼
```

에이전트 응답:

```text
VirtualBox VM의 SSH 문제는 VM 네트워크 모드에 따라 진단이 달라집니다.

먼저 VM의 네트워크 모드가 NAT, Bridge, Host-only 중 무엇인지 확인하세요.

- NAT 모드: 호스트에서 VM으로 접속하려면 포트포워딩이 필요할 수 있습니다.
- Bridge 모드: VM이 실제 LAN의 IP를 받으므로 그 IP로 직접 SSH 접속할 수 있습니다.
- Host-only 모드: 호스트와 VM 사이의 내부망에서만 접속할 수 있습니다.

VM 내부에서는 다음을 확인하세요.

`ip addr`
`ip route`
`systemctl status sshd`
`ss -tulnp | grep ':22'`

NAT 모드에서 포트포워딩을 `Host 2222 -> Guest 22`로 설정했다면 호스트에서는 다음처럼 접속합니다.

`ssh -p 2222 user@127.0.0.1`
```

---

## 주의할 점

SSH 문제를 진단할 때 다음을 주의해야 한다.

1. ping 성공은 SSH 접속 성공을 의미하지 않는다.
2. ping 실패도 SSH 불가능을 확정하지 않는다. ICMP만 차단될 수 있다.
3. `Connection timed out`과 `Connection refused`는 원인 방향이 다르다.
4. `Connection refused`는 sshd 미실행 또는 포트 미리스닝 가능성이 크다.
5. `Connection timed out`은 방화벽, 보안 그룹, NAT, 라우팅 문제 가능성이 크다.
6. `Permission denied`는 네트워크가 아니라 인증 문제일 가능성이 높다.
7. SSH 포트를 변경하면 sshd_config, 방화벽, SELinux, 보안 그룹을 모두 수정해야 한다.
8. root 로그인은 기본적으로 막혀 있을 수 있다.
9. 비밀번호 로그인이 막혀 있으면 키 인증을 사용해야 한다.
10. SSH key는 파일 권한이 너무 열려 있으면 무시될 수 있다.
11. 클라우드 서버는 OS 방화벽과 클라우드 보안 그룹을 모두 확인해야 한다.
12. 공유기 뒤 서버는 포트포워딩과 공인 IP 여부를 확인해야 한다.
13. CGNAT 환경에서는 일반 포트포워딩이 안 될 수 있다.
14. VM NAT 모드에서는 SSH 포트포워딩이 필요할 수 있다.
15. OpenWrt는 OpenSSH가 아니라 Dropbear를 사용할 수 있다.
16. `Host key verification failed`는 보안 경고이므로 서버 변경 여부를 확인해야 한다.
17. 특정 네트워크에서만 SSH가 안 되면 중간 네트워크의 TCP 22 차단 가능성이 있다.
18. fail2ban이 특정 IP를 차단할 수 있다.
19. 원격으로 sshd_config를 바꿀 때는 기존 세션을 끊지 말고 새 접속 테스트를 먼저 해야 한다.
20. DB나 운영 서버의 SSH를 0.0.0.0/0 전체에 여는 것은 보안상 위험하다.

---

## 빠른 진단 요약

```text
1. 접속 명령어, IP, 포트, 사용자명 확인
2. ping <server_ip>로 기본 도달성 확인
3. nc -vz <server_ip> 22 또는 Test-NetConnection으로 포트 확인
4. 오류가 timeout인지 refused인지 permission denied인지 구분
5. 서버에서 systemctl status sshd 또는 systemctl status ssh 확인
6. ss -tulnp | grep :22로 포트 listen 확인
7. 서버 방화벽 확인
8. 클라우드 보안 그룹 또는 네트워크 ACL 확인
9. 공유기 뒤 서버라면 포트포워딩과 공인 IP 확인
10. ssh -v로 인증 과정 확인
11. 서버 로그 journalctl 또는 auth.log/secure 확인
12. 키 인증이면 private key, authorized_keys, 권한 확인
13. sshd_config에서 Port, PermitRootLogin, PasswordAuthentication 확인
14. 필요 시 tcpdump로 SSH 패킷 도착 여부 확인
```

---

## 핵심 키워드

SSH, SSH Troubleshooting, ssh 접속 안 됨, PuTTY 접속 안 됨, PowerShell ssh, OpenSSH, Dropbear, TCP 22, sshd, ssh service, systemctl status sshd, systemctl status ssh, ss -tulnp, netstat, firewall-cmd --list-all, ufw, iptables, nftables, SSH timeout, Connection timed out, Connection refused, Permission denied, Permission denied publickey, No route to host, Network is unreachable, Could not resolve hostname, Host key verification failed, REMOTE HOST IDENTIFICATION HAS CHANGED, known_hosts, ssh-keygen -R, private key, public key, authorized_keys, chmod 600, chmod 700, ssh -v, ssh -vvv, ssh -i, IdentitiesOnly, sshd_config, Port, ListenAddress, PermitRootLogin, PasswordAuthentication, PubkeyAuthentication, AllowUsers, DenyUsers, MaxAuthTries, Too many authentication failures, no matching host key type, no matching key exchange method, fail2ban, SELinux ssh_port_t, semanage port, 클라우드 보안 그룹, Security Group, Network ACL, 포트포워딩, NAT, CGNAT, VirtualBox SSH, VMware SSH, WSL SSH, Docker SSH, OpenWrt SSH, dropbear, tcpdump port 22.