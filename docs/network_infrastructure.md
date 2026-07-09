# Network Infrastructure Troubleshooting

## 문서 목적

이 문서는 네트워크 트러블슈팅 에이전트가 스위치, 라우터, 케이블, 무선 AP, VLAN, 포트 상태, 링크 속도, 장비 과부하, 대역폭 부족, 패킷 손실, 지연 시간, 중간 장비 병목, QoS, 네트워크 정책 문제를 진단할 때 참고하기 위한 RAG 지식 문서이다.

네트워크 인프라 문제는 특정 PC나 특정 서비스 하나의 문제가 아니라, 네트워크를 구성하는 물리적 장비와 경로 전체에서 발생하는 문제를 의미한다. 사용자는 보통 "인터넷이 느리다", "가끔 끊긴다", "특정 자리에서만 안 된다", "회의실 Wi-Fi만 이상하다", "서버는 정상인데 어떤 구간에서만 접속이 안 된다"처럼 표현한다.

에이전트는 사용자의 증상을 듣고 먼저 다음을 구분해야 한다.

- 한 장비만 문제인지
- 같은 구역의 여러 장비가 문제인지
- 유선만 문제인지
- 무선만 문제인지
- 특정 VLAN만 문제인지
- 특정 스위치 아래 장비만 문제인지
- 특정 라우터 또는 게이트웨이 이후부터 문제인지
- 특정 서비스만 문제인지
- 전체 네트워크 품질 문제인지
- 물리 계층 문제인지
- L2 스위칭 문제인지
- L3 라우팅 문제인지
- 방화벽/정책 문제인지
- 대역폭 또는 장비 부하 문제인지

네트워크 인프라 문제를 정확히 판단하려면 `문제가 발생하는 위치`, `영향 범위`, `유선/무선 여부`, `IP 설정`, `게이트웨이`, `VLAN`, `스위치 포트`, `링크 상태`, `패킷 손실률`, `지연 시간`, `traceroute 결과`, `장비 CPU/메모리/인터페이스 사용률`, `에러 카운터`, `최근 변경 사항`을 함께 확인해야 한다.

---

## 관련 사용자 표현

사용자는 네트워크 인프라라는 용어를 직접 말하지 않을 수 있다. 다음 표현은 인프라 계층 문제와 관련될 가능성이 있다.

- 네트워크가 느려
- 인터넷이 너무 느려
- 가끔 끊겨
- 간헐적으로 연결이 끊긴다
- 특정 자리에서만 인터넷이 안 된다
- 특정 방에서만 Wi-Fi가 안 된다
- 회의실 Wi-Fi만 이상하다
- 같은 공유기인데 어떤 PC만 느리다
- 같은 서버인데 위치에 따라 접속이 다르다
- 사무실 일부 구역만 안 된다
- 특정 스위치에 연결된 장비만 안 된다
- 특정 VLAN만 안 된다
- 랜선을 바꾸면 될까?
- 케이블 문제인가?
- 스위치 포트가 죽은 것 같아
- 포트에 불은 들어오는데 통신이 안 된다
- 링크는 살아 있는데 느리다
- 100Mbps로 잡혀
- 기가비트가 안 잡힌다
- 패킷 손실이 있다
- ping이 튄다
- 지연 시간이 너무 높다
- traceroute가 특정 구간에서 멈춘다
- 특정 홉 이후로 안 간다
- 라우터 문제인가?
- 스위치 문제인가?
- AP 문제인가?
- 무선 신호는 강한데 인터넷이 느리다
- DHCP는 받았는데 통신이 안 된다
- 게이트웨이는 되는데 외부가 느리다
- 특정 시간대에만 느리다
- 사람이 많을 때만 느리다
- 업로드만 느리다
- 다운로드만 느리다
- 화상회의가 끊긴다
- 게임 핑이 튄다
- 서버 접속이 자주 끊긴다
- 네트워크 장비가 과부하인 것 같다
- QoS 문제인가?
- 방화벽 장비가 병목인가?
- 중간 장비에서 막히는 것 같다
- 같은 서비스인데 집에서는 되고 학교에서는 안 된다
- 회사망에서만 안 된다
- 모바일 핫스팟에서는 되는데 사무실망에서는 안 된다

---

## 핵심 개념

네트워크 인프라는 단순히 PC 한 대의 설정이 아니라, 여러 장비와 계층이 연결된 전체 구조를 의미한다.

일반적인 네트워크 경로는 다음과 같다.

```text
Client PC
  ↓
NIC / Wi-Fi Adapter
  ↓
Cable or Wireless Link
  ↓
Access Switch or Wi-Fi AP
  ↓
Distribution Switch / L3 Switch
  ↓
Router or Firewall
  ↓
ISP or WAN
  ↓
Internet / Remote Server
```

문제가 발생하면 어느 구간에서 끊기는지 확인해야 한다.

예를 들어 웹사이트 접속 실패는 다음 중 하나일 수 있다.

```text
PC NIC 문제
케이블 문제
스위치 포트 문제
VLAN 문제
DHCP 문제
게이트웨이 문제
라우팅 문제
방화벽 정책 문제
DNS 문제
ISP 문제
원격 서버 문제
```

따라서 네트워크 인프라 문제를 진단할 때는 "인터넷이 안 된다"는 결과만 보지 말고, 문제 범위와 경로를 단계적으로 좁혀야 한다.

---

## OSI 계층 기준으로 보는 인프라 문제

네트워크 문제는 OSI 계층 기준으로 나누면 더 쉽게 진단할 수 있다.

### Layer 1: 물리 계층

케이블, 포트, 광모듈, 전원, 무선 신호, 링크 상태와 관련된다.

대표 문제:

```text
케이블 불량
랜 포트 고장
스위치 포트 고장
광모듈 불량
링크 down
링크 속도 불일치
무선 신호 약함
간섭
전원 문제
```

### Layer 2: 데이터링크 계층

MAC 주소, 스위칭, VLAN, STP, 링크 aggregation, ARP와 관련된다.

대표 문제:

```text
VLAN 오설정
스위치 MAC 테이블 문제
STP blocking
Loop 발생
ARP 실패
포트 보안
trunk VLAN 누락
native VLAN 불일치
```

### Layer 3: 네트워크 계층

IP 주소, 서브넷, 게이트웨이, 라우팅, ACL과 관련된다.

대표 문제:

```text
IP 설정 오류
서브넷 마스크 오류
기본 게이트웨이 오류
라우팅 테이블 문제
VLAN 간 라우팅 누락
ACL 차단
NAT 문제
```

### Layer 4 이상

포트, 방화벽, TCP/UDP, 애플리케이션 서비스와 관련된다.

대표 문제:

```text
방화벽 포트 차단
서비스 미실행
포트 미리스닝
프록시 문제
TLS 문제
애플리케이션 오류
```

네트워크 인프라 문서는 주로 L1~L3와 장비 상태를 다루며, 특정 포트 문제는 `firewall_ports.md`, DNS 문제는 `dns_troubleshooting.md`, DHCP 문제는 `dhcp_troubleshooting.md`, 게이트웨이/라우팅 문제는 `gateway_routing.md`도 함께 참고해야 한다.

---

## 문제 범위 파악이 중요한 이유

인프라 문제에서 가장 중요한 것은 영향을 받는 범위를 파악하는 것이다.

### 한 장비만 문제

가능한 원인:

```text
해당 PC의 NIC 문제
케이블 문제
IP 설정 문제
방화벽 문제
드라이버 문제
OS 네트워크 스택 문제
Wi-Fi 어댑터 문제
```

### 같은 스위치에 연결된 장비들이 모두 문제

가능한 원인:

```text
해당 스위치 장애
스위치 uplink 문제
스위치 포트/VLAN 설정 문제
전원 문제
스위치 과부하
uplink 대역폭 부족
```

### 특정 VLAN만 문제

가능한 원인:

```text
VLAN 설정 오류
trunk 허용 VLAN 누락
SVI down
DHCP relay 문제
inter-VLAN routing 문제
ACL 정책 문제
```

### 전체 사무실이 문제

가능한 원인:

```text
공유기/라우터 장애
방화벽 장애
ISP 회선 문제
DNS/DHCP 서버 장애
코어 스위치 장애
전원 장애
```

### 특정 서비스만 문제

가능한 원인:

```text
방화벽 포트 차단
서버 서비스 장애
DNS 문제
프록시 문제
애플리케이션 문제
```

### 특정 시간대에만 문제

가능한 원인:

```text
대역폭 부족
사용자 증가
백업/동기화 트래픽
장비 CPU/메모리 과부하
QoS 정책 문제
ISP 혼잡
무선 채널 혼잡
```

---

## 네트워크 인프라 문제의 대표 증상

### 1. 네트워크 속도가 느림

가능한 원인:

```text
대역폭 부족
스위치 uplink 병목
라우터 또는 방화벽 과부하
Wi-Fi 간섭
링크 속도 100Mbps 협상
케이블 품질 문제
duplex mismatch
패킷 손실
QoS 정책 문제
백업/업데이트 트래픽 증가
브로드캐스트/멀티캐스트 과다
장비 CPU/메모리 부족
ISP 회선 혼잡
```

판단 기준:

```text
특정 PC만 느림:
PC, 케이블, NIC, 드라이버 문제 가능성.

같은 스위치 아래 모든 장비가 느림:
스위치 uplink 또는 스위치 자체 문제 가능성.

무선만 느림:
Wi-Fi AP, 채널 간섭, 신호 세기, 접속자 수 문제 가능성.

특정 시간대에만 느림:
대역폭 사용량, 트래픽 폭증, 백업 작업, ISP 혼잡 가능성.
```

---

### 2. 간헐적으로 연결이 끊김

가능한 원인:

```text
케이블 접촉 불량
스위치 포트 불량
NIC 절전 모드
Wi-Fi 로밍 문제
무선 간섭
DHCP lease 갱신 문제
STP topology change
라우터 과부하
방화벽 세션 테이블 고갈
IP 충돌
ARP 충돌
전원 불안정
장비 재부팅
```

진단 방향:

```text
끊기는 시간이 규칙적인가?
특정 장비만 끊기는가?
같은 구역 장비가 동시에 끊기는가?
유선과 무선 모두 끊기는가?
장비 로그에 link up/down이 있는가?
ping 손실이 발생하는가?
```

---

### 3. 특정 구간을 지나면 통신이 실패함

예시:

```text
1번 홉 게이트웨이까지는 성공
2번 홉 이후 실패
특정 라우터 이후로 traceroute가 멈춤
```

가능한 원인:

```text
중간 라우터 장애
방화벽 정책 차단
라우팅 누락
NAT 문제
ACL 차단
ISP 문제
return route 누락
MTU 문제
```

진단:

```bash
traceroute <target_ip>
tracert <target_ip>
ping <gateway_ip>
ping <next_hop_ip>
```

판단:

```text
첫 번째 홉부터 실패:
클라이언트와 게이트웨이 사이 문제 가능성.

게이트웨이 이후 실패:
라우터, 방화벽, NAT, ISP 문제 가능성.

특정 중간 홉에서만 별표:
ICMP 응답 차단일 수도 있으므로 실제 서비스 접속 여부와 함께 판단해야 함.
```

---

### 4. 같은 서비스라도 위치에 따라 접속 성공 여부가 다름

예시:

```text
집에서는 접속됨
학교에서는 안 됨
모바일 핫스팟에서는 됨
회사 Wi-Fi에서는 안 됨
특정 VLAN에서는 안 됨
```

가능한 원인:

```text
네트워크 정책 차이
방화벽 ACL
DNS 차이
프록시 설정
VLAN 정책
NAT 정책
보안 장비 차단
포트 차단
내부/외부 DNS 차이
```

판단:

```text
위치에 따라 결과가 다르면 서버 자체 문제보다 중간 네트워크 정책, 라우팅, DNS, 방화벽 차이를 의심해야 한다.
```

---

### 5. 특정 스위치에 연결된 장비만 문제

가능한 원인:

```text
스위치 uplink 장애
스위치 포트 VLAN 오설정
스위치 전원 문제
스위치 과부하
MAC 테이블 문제
STP blocking
루프 발생
trunk VLAN 누락
uplink 케이블 불량
```

확인할 것:

```text
해당 스위치 아래 모든 장비가 문제인가?
다른 스위치에 연결하면 정상인가?
스위치 uplink LED가 정상인가?
해당 포트의 VLAN이 맞는가?
스위치 로그에 link flap이 있는가?
```

---

### 6. Wi-Fi만 느리거나 끊김

가능한 원인:

```text
무선 신호 약함
채널 간섭
AP 과부하
동시 접속자 수 과다
2.4GHz 혼잡
5GHz 범위 부족
벽/장애물 영향
로밍 문제
AP uplink 문제
DHCP 문제
인증 문제
전파 간섭
```

판단:

```text
유선은 정상 + 무선만 문제:
AP, 무선 신호, 채널, 간섭 문제 가능성.

특정 위치에서만 무선 문제:
신호 세기, 장애물, AP 배치 문제 가능성.

사람 많을 때만 문제:
AP 동시 접속자 수, 무선 대역폭, QoS 문제 가능성.
```

---

### 7. 링크는 살아 있는데 속도가 낮음

예시:

```text
기가비트 장비인데 100Mbps로 연결됨
1Gbps가 아니라 100Mbps로 협상됨
```

가능한 원인:

```text
랜 케이블 불량
Cat5 이하 케이블
커넥터 접촉 불량
스위치 포트 문제
NIC 설정 문제
자동 협상 실패
duplex mismatch
케이블 길이 과다
```

확인:

Linux:

```bash
ethtool <interface>
```

Windows:

```text
네트워크 어댑터 상태에서 링크 속도 확인
```

판단:

```text
1Gbps 지원 장비인데 100Mbps로 잡히면 케이블, 포트, 자동 협상 문제를 먼저 의심한다.
```

---

## 물리 계층 문제

물리 계층은 가장 기본이지만 실제 장애 원인으로 매우 흔하다.

### 가능한 원인

```text
랜 케이블 불량
케이블 단선
커넥터 접촉 불량
스위치 포트 고장
NIC 고장
광모듈 불량
전원 문제
PoE 전원 부족
케이블 길이 초과
케이블 규격 부족
장비 과열
```

### 대표 증상

```text
링크 LED가 꺼짐
인터페이스가 down 상태
간헐적으로 link up/down 반복
속도가 100Mbps로만 잡힘
패킷 손실 발생
특정 자리에서만 문제 발생
케이블을 건드리면 연결이 끊김
```

### Linux 확인 명령어

```bash
ip link
ip addr
ethtool <interface>
dmesg | grep -i link
journalctl -k | grep -i link
```

예시:

```bash
ethtool eth0
```

확인할 항목:

```text
Link detected: yes/no
Speed: 1000Mb/s or 100Mb/s
Duplex: Full/Half
Auto-negotiation
```

### Windows 확인 방법

```text
네트워크 어댑터 상태
링크 속도 확인
장치 관리자에서 NIC 상태 확인
이벤트 뷰어에서 네트워크 어댑터 로그 확인
```

### 해결 방향

```text
케이블 교체
스위치 포트 변경
NIC 드라이버 업데이트
다른 장비로 교차 테스트
광모듈 교체
장비 재부팅
PoE 예산 확인
케이블 길이와 규격 확인
```

---

## 스위치 문제

스위치는 같은 LAN 내부의 장비들을 연결하는 L2 장비이다. 스위치 문제가 발생하면 같은 구역의 여러 장비가 동시에 영향을 받을 수 있다.

### 가능한 원인

```text
스위치 포트 불량
uplink 포트 장애
VLAN 오설정
trunk 설정 오류
MAC 주소 테이블 문제
STP blocking
loop 발생
브로드캐스트 스톰
포트 보안 차단
스위치 CPU 과부하
전원 문제
펌웨어 문제
```

### 대표 증상

```text
특정 포트만 안 됨
특정 스위치 아래 장비만 안 됨
특정 VLAN만 안 됨
링크가 자주 끊김
내부 통신이 느림
브로드캐스트가 과다함
스위치가 자주 재부팅됨
```

### 확인할 항목

```text
포트 link up/down 상태
포트 speed/duplex
포트 error counter
VLAN membership
trunk allowed VLAN
STP 상태
MAC address table
포트 security 상태
uplink 사용률
CPU/Memory 사용률
```

### 판단 기준

```text
한 포트만 문제:
케이블, 포트, 단말 NIC 문제 가능성.

스위치 전체가 문제:
스위치 전원, uplink, 장비 과부하 가능성.

특정 VLAN만 문제:
VLAN/trunk/SVI/ACL 문제 가능성.

uplink 사용률이 높음:
대역폭 병목 가능성.
```

---

## 라우터/L3 스위치 문제

라우터와 L3 스위치는 서로 다른 네트워크 간 통신을 담당한다.

### 가능한 원인

```text
라우팅 테이블 오류
default route 누락
static route 오류
dynamic routing 장애
VLAN SVI down
inter-VLAN routing 미설정
ACL 차단
NAT 문제
방화벽 정책
CPU 과부하
인터페이스 down
WAN 회선 문제
```

### 대표 증상

```text
같은 LAN은 되지만 외부망이 안 됨
VLAN 간 통신이 안 됨
특정 대역만 안 됨
traceroute가 게이트웨이 이후 멈춤
게이트웨이는 되지만 인터넷이 안 됨
```

### 확인할 항목

```text
인터페이스 상태
라우팅 테이블
default route
NAT 설정
ACL 정책
VLAN SVI 상태
CPU/Memory 사용률
WAN 상태
```

관련 문서:

```text
gateway_routing.md
firewall_ports.md
```

---

## 무선 AP 문제

무선 네트워크는 유선보다 환경 영향을 많이 받는다.

### 가능한 원인

```text
신호 약함
채널 간섭
AP 과부하
동시 접속자 수 과다
2.4GHz 혼잡
5GHz 범위 부족
인증 서버 문제
DHCP 문제
AP uplink 문제
로밍 문제
전원/PoE 문제
```

### 대표 증상

```text
Wi-Fi 연결은 되지만 인터넷이 느림
특정 위치에서만 끊김
신호는 강한데 속도가 느림
사람이 많을 때 느림
유선은 정상인데 무선만 문제
특정 SSID만 문제
```

### 진단 방향

```text
유선 연결은 정상인지 비교
다른 SSID에서도 같은지 확인
AP 근처와 먼 곳에서 비교
2.4GHz/5GHz 차이 확인
동시 접속자 수 확인
AP uplink 상태 확인
DHCP lease 확인
무선 채널 혼잡 확인
```

---

## 대역폭 부족과 병목

네트워크가 느릴 때는 단순히 "인터넷이 안 좋다"가 아니라 어느 구간이 병목인지 찾아야 한다.

### 병목이 발생할 수 있는 위치

```text
PC NIC
랜 케이블
Access Switch 포트
Switch uplink
Router WAN
Firewall
VPN tunnel
ISP 회선
서버 NIC
서버 디스크/CPU
```

### 대표 증상

```text
특정 시간대에 느림
많은 사용자가 동시에 쓸 때 느림
파일 다운로드가 느림
화상회의가 끊김
ping 지연 시간이 증가
패킷 손실 발생
```

### 확인할 항목

```text
링크 속도
인터페이스 사용률
패킷 손실률
지연 시간
CPU/Memory 사용률
QoS 정책
트래픽 상위 사용자
백업/동기화 작업
```

### Linux에서 기본 확인

```bash
ping <target_ip>
traceroute <target_ip>
ip -s link
ss -s
```

`ip -s link`는 인터페이스별 RX/TX 패킷, 에러, 드롭 카운터를 볼 수 있다.

---

## 패킷 손실 문제

패킷 손실은 네트워크 품질 저하의 대표 원인이다.

### 증상

```text
ping 중간중간 실패
화상회의 끊김
게임 핑 튐
SSH 세션 끊김
웹페이지 로딩 지연
파일 전송 속도 저하
```

### 원인

```text
무선 간섭
케이블 불량
스위치 포트 에러
장비 과부하
대역폭 포화
QoS 정책 문제
ISP 품질 문제
방화벽 세션 처리 한계
```

### 확인 명령어

```bash
ping -c 100 <target_ip>
```

Windows:

```cmd
ping -n 100 <target_ip>
```

판단:

```text
게이트웨이 ping에서 손실:
내부 LAN, Wi-Fi, 케이블, 스위치 문제 가능성.

외부 IP에서만 손실:
게이트웨이 이후, ISP, WAN, 방화벽 문제 가능성.

특정 서버에서만 손실:
목적지 서버 또는 해당 경로 문제 가능성.
```

---

## 지연 시간 증가 문제

지연 시간은 패킷이 목적지까지 갔다가 돌아오는 데 걸리는 시간이다.

### 원인

```text
네트워크 혼잡
무선 품질 저하
라우터/방화벽 과부하
QoS 정책
VPN 터널
원거리 서버
ISP 경로 문제
패킷 큐잉 지연
```

### 확인

```bash
ping <target_ip>
traceroute <target_ip>
```

Windows:

```cmd
ping <target_ip>
tracert <target_ip>
```

판단:

```text
게이트웨이 ping부터 지연이 큼:
로컬 네트워크 문제 가능성.

게이트웨이는 빠른데 외부에서 지연 증가:
WAN, ISP, 중간 경로 문제 가능성.

특정 서비스만 느림:
애플리케이션 서버, DNS, 포트, 프록시 문제 가능성.
```

---

## MTU 문제

MTU는 한 번에 전송할 수 있는 패킷 크기이다. MTU 문제가 있으면 작은 패킷은 되지만 큰 패킷이나 특정 서비스가 실패할 수 있다.

### 대표 증상

```text
ping은 되는데 웹사이트 일부가 안 열림
VPN 연결 후 특정 사이트 접속 안 됨
파일 업로드 실패
일부 HTTPS 사이트만 느림
SSH는 되는데 대용량 전송 실패
```

### 원인

```text
VPN 터널 MTU 감소
PPPoE 환경
ICMP Fragmentation Needed 차단
Path MTU Discovery 실패
방화벽에서 ICMP 차단
```

### 확인 예시

Linux:

```bash
ping -M do -s 1472 8.8.8.8
```

Windows:

```cmd
ping 8.8.8.8 -f -l 1472
```

판단:

```text
작은 크기는 성공하고 큰 크기는 실패:
MTU 문제 가능성.
```

주의:

MTU 문제는 일반적인 초급 진단에서는 자주 보지 않지만, VPN이나 터널 환경에서는 중요하다.

---

## QoS와 네트워크 정책 문제

QoS는 트래픽 우선순위를 조정하는 기능이다. 잘못 설정되면 특정 트래픽이 느려지거나 끊길 수 있다.

### 가능한 문제

```text
음성/화상 트래픽 우선순위 미설정
특정 포트 대역폭 제한
특정 VLAN 대역폭 제한
업로드 트래픽이 다운로드를 방해
백업 트래픽이 업무 트래픽을 압도
정책 기반 라우팅 오류
```

### 증상

```text
화상회의만 끊김
파일 다운로드 중 전체 인터넷 느려짐
특정 서비스만 느림
특정 부서/VLAN만 느림
업무 시간에만 느림
```

### 판단 방향

```text
시간대별 문제인지 확인
특정 애플리케이션만 문제인지 확인
트래픽 사용량 확인
QoS 정책 변경 이력 확인
```

---

## 브로드캐스트 스톰과 루프

L2 네트워크에서 루프가 발생하면 브로드캐스트 트래픽이 폭증하여 네트워크 전체가 느려지거나 마비될 수 있다.

### 원인

```text
스위치 간 케이블을 잘못 연결
STP 비활성화
허브 연결
잘못된 이중 연결
무단 공유기/스위치 연결
```

### 증상

```text
네트워크 전체가 갑자기 느려짐
스위치 CPU 상승
브로드캐스트 트래픽 폭증
링크 LED가 비정상적으로 빠르게 깜빡임
여러 장비가 동시에 끊김
```

### 확인할 항목

```text
STP 상태
스위치 로그
브로드캐스트 패킷 수
최근 케이블 연결 변경
무단 스위치 연결 여부
```

---

## IP 충돌 문제

같은 네트워크에 동일한 IP를 가진 장비가 두 대 이상 있으면 통신이 불안정해질 수 있다.

### 증상

```text
간헐적으로 접속됨
가끔 게이트웨이 통신 실패
특정 IP가 두 장비로 오감
ARP 테이블이 자주 바뀜
Windows에서 IP 충돌 경고
```

### 원인

```text
수동 IP 중복 설정
DHCP pool과 static IP 범위 중복
DHCP 예약 오류
Rogue DHCP
VM 복제 후 동일 IP 사용
```

### 확인

Linux:

```bash
ip neigh
arp -a
```

Windows:

```cmd
arp -a
```

패킷 캡처:

```bash
sudo tcpdump -i <interface> -n arp
```

해결:

```text
중복 IP 장비 확인
DHCP pool과 static IP 범위 분리
수동 IP 변경
DHCP lease 확인
Rogue DHCP 제거
```

---

## Recommended Commands

네트워크 인프라 문제는 운영체제별, 장비별로 확인 명령어가 다르다.

---

## 공통 진단 명령어

### 기본 연결 확인

```bash
ping <target_ip>
```

예시:

```bash
ping <gateway_ip>
ping 8.8.8.8
ping google.com
```

### 경로 확인

Linux:

```bash
traceroute <target_ip>
```

Windows:

```cmd
tracert <target_ip>
```

대체:

```bash
tracepath <target_ip>
```

### 라우팅 확인

Linux:

```bash
ip route
```

Windows:

```cmd
route print
```

### DNS와 구분

```bash
nslookup google.com
```

Linux:

```bash
dig google.com
```

### 포트와 구분

```bash
nc -vz <server_ip> <port>
```

Windows PowerShell:

```powershell
Test-NetConnection <server_ip> -Port <port>
```

---

## Linux 진단 명령어

### IP와 인터페이스 확인

```bash
ip addr
ip link
```

### 인터페이스 통계 확인

```bash
ip -s link
```

확인할 항목:

```text
RX errors
TX errors
dropped
overruns
carrier errors
collisions
```

### 라우팅 확인

```bash
ip route
ip route get <destination_ip>
```

### ARP/Neighbor 확인

```bash
ip neigh
```

### 링크 속도 확인

```bash
ethtool <interface>
```

예시:

```bash
ethtool eth0
ethtool ens33
ethtool enp0s3
```

### 커널 로그에서 링크 이벤트 확인

```bash
dmesg | grep -i link
journalctl -k | grep -i link
```

### 네트워크 연결 상태 확인

```bash
ss -s
ss -tulnp
```

### 패킷 캡처

```bash
sudo tcpdump -i <interface> -n
```

특정 대상:

```bash
sudo tcpdump -i <interface> -n host <target_ip>
```

ARP 확인:

```bash
sudo tcpdump -i <interface> -n arp
```

ICMP 확인:

```bash
sudo tcpdump -i <interface> -n icmp
```

---

## Windows 진단 명령어

### IP 설정 확인

```cmd
ipconfig /all
```

### 라우팅 테이블 확인

```cmd
route print
```

### ARP 테이블 확인

```cmd
arp -a
```

### ping 테스트

```cmd
ping <target_ip>
ping -n 100 <target_ip>
```

### 경로 추적

```cmd
tracert <target_ip>
```

### 포트 확인

```cmd
netstat -ano
```

### 특정 포트 테스트

PowerShell:

```powershell
Test-NetConnection <server_ip> -Port <port>
```

### 네트워크 어댑터 상태

```powershell
Get-NetAdapter
```

### 네트워크 어댑터 통계

```powershell
Get-NetAdapterStatistics
```

---

## OpenWrt 진단 명령어

OpenWrt 기반 라우터에서는 다음을 확인한다.

### 인터페이스 확인

```sh
ip addr
ip link
ip route
```

### UCI 설정 확인

```sh
uci show network
uci show wireless
uci show dhcp
uci show firewall
```

### WAN/LAN 상태 확인

```sh
ifstatus wan
ifstatus lan
```

### DHCP lease 확인

```sh
cat /tmp/dhcp.leases
```

### 로그 확인

```sh
logread
```

DNS/DHCP 관련:

```sh
logread | grep dnsmasq
```

무선 관련:

```sh
logread | grep hostapd
logread | grep wlan
```

### 트래픽/인터페이스 통계

```sh
cat /proc/net/dev
```

### ping/traceroute

```sh
ping 8.8.8.8
traceroute 8.8.8.8
```

확인할 항목:

```text
WAN이 IP를 받았는가?
default route가 있는가?
LAN 클라이언트가 DHCP를 받는가?
LAN -> WAN forwarding이 허용되는가?
WAN masquerading이 켜져 있는가?
무선 AP가 정상 동작하는가?
```

---

## Wireshark / Packet Capture 활용

Wireshark나 tcpdump는 문제가 어느 계층에서 발생하는지 확인하는 데 매우 유용하다.

### 확인 가능한 것

```text
ARP 요청/응답
DHCP Discover/Offer/Request/ACK
DNS Query/Response
TCP SYN/SYN-ACK/RST
ICMP Echo Request/Reply
패킷 재전송
브로드캐스트 과다
특정 포트 통신
```

### 상황별 필터

ARP:

```text
arp
```

DHCP:

```text
bootp
```

DNS:

```text
dns
```

ICMP:

```text
icmp
```

특정 IP:

```text
ip.addr == 192.168.1.10
```

특정 TCP 포트:

```text
tcp.port == 80
tcp.port == 443
tcp.port == 22
```

### 판단 기준

```text
ARP 응답이 없음:
L2 연결, VLAN, 게이트웨이 문제 가능성.

DHCP Offer가 없음:
DHCP 서버, relay, VLAN 문제 가능성.

DNS Query는 있는데 Response가 없음:
DNS 서버, 방화벽, 라우팅 문제 가능성.

TCP SYN만 반복:
방화벽 drop, 경로 문제 가능성.

TCP RST가 옴:
포트 닫힘, 서비스 미실행 가능성.

패킷 재전송이 많음:
손실, 혼잡, 장비 부하 가능성.
```

---

## 단계별 진단 절차

네트워크 인프라 문제는 다음 순서로 진단하는 것이 좋다.

---

### 1단계: 영향 범위 확인

먼저 문제가 누구에게 발생하는지 확인한다.

확인 질문:

```text
한 장비만 문제인가?
여러 장비가 동시에 문제인가?
특정 위치만 문제인가?
유선만 문제인가?
무선만 문제인가?
특정 VLAN만 문제인가?
특정 시간대에만 문제인가?
특정 서비스만 문제인가?
```

판단:

```text
한 장비만 문제:
클라이언트, 케이블, NIC, OS 설정 문제 가능성.

여러 장비가 동시에 문제:
스위치, AP, 라우터, DHCP/DNS, 회선 문제 가능성.

특정 위치만 문제:
케이블, 스위치 포트, AP 커버리지, VLAN 문제 가능성.

특정 시간대만 문제:
대역폭 부족, 트래픽 폭증, 장비 과부하 가능성.
```

---

### 2단계: 물리 연결 확인

확인할 것:

```text
케이블 연결 상태
링크 LED
포트 변경 시 정상 여부
다른 케이블 사용 시 정상 여부
Wi-Fi 신호 세기
AP 연결 여부
NIC 활성화 여부
```

Linux:

```bash
ip link
ethtool <interface>
```

Windows:

```powershell
Get-NetAdapter
```

---

### 3단계: IP 설정 확인

Windows:

```cmd
ipconfig /all
```

Linux:

```bash
ip addr
ip route
```

확인할 것:

```text
IP 주소가 있는가?
169.254.x.x가 아닌가?
서브넷 마스크가 맞는가?
기본 게이트웨이가 있는가?
DNS 서버가 있는가?
```

---

### 4단계: 게이트웨이까지 확인

```bash
ping <gateway_ip>
```

판단:

```text
게이트웨이 ping 실패:
로컬 네트워크, VLAN, 케이블, 스위치, ARP 문제 가능성.

게이트웨이 ping 성공:
게이트웨이까지는 도달 가능. 이후 경로를 확인한다.
```

---

### 5단계: 외부 IP 확인

```bash
ping 8.8.8.8
```

판단:

```text
게이트웨이는 되는데 외부 IP 실패:
라우터, NAT, WAN, 방화벽, ISP 문제 가능성.

외부 IP 성공:
기본 인터넷 연결은 가능. DNS 또는 서비스 문제를 확인한다.
```

---

### 6단계: DNS와 포트 문제 분리

DNS 확인:

```bash
nslookup google.com
```

포트 확인:

```bash
nc -vz <server_ip> <port>
```

판단:

```text
IP는 되는데 도메인 실패:
DNS 문제.

IP와 도메인은 되는데 특정 서비스 실패:
포트/방화벽/서비스 문제.
```

---

### 7단계: 경로 확인

Linux:

```bash
traceroute <target_ip>
```

Windows:

```cmd
tracert <target_ip>
```

판단:

```text
첫 홉 실패:
클라이언트와 게이트웨이 사이 문제.

중간 홉 이후 실패:
라우팅, 방화벽, ISP, 중간 장비 문제.

특정 홉에서 지연 증가:
해당 구간 병목 가능성.
```

---

### 8단계: 인터페이스 에러와 장비 부하 확인

Linux:

```bash
ip -s link
ethtool <interface>
```

확인할 것:

```text
RX errors
TX errors
dropped packets
collisions
carrier errors
speed/duplex
```

장비에서 확인할 것:

```text
CPU 사용률
메모리 사용률
인터페이스 사용률
에러 카운터
drop 카운터
로그
```

---

### 9단계: 위치별 비교 테스트

문제가 위치에 따라 다르면 비교가 중요하다.

비교 예시:

```text
같은 PC를 다른 포트에 연결
같은 케이블로 다른 PC 연결
다른 케이블 사용
유선과 무선 비교
다른 AP에 연결
다른 VLAN에서 테스트
모바일 핫스팟과 비교
```

판단:

```text
PC를 옮기면 정상:
원래 위치의 케이블/포트/AP 문제 가능성.

다른 PC도 같은 자리에서 문제:
인프라 문제 가능성.

모바일 핫스팟에서는 정상:
원래 네트워크 정책, DNS, 방화벽, 라우팅 문제 가능성.
```

---

## 판단 기준 요약

에이전트는 다음 기준으로 원인을 좁힐 수 있다.

```text
한 장비만 문제:
클라이언트 설정, NIC, 케이블, OS 방화벽 문제 가능성이 높다.

같은 위치의 여러 장비가 문제:
스위치 포트, AP, 케이블링, VLAN, uplink 문제 가능성이 높다.

같은 스위치 아래 장비가 모두 문제:
스위치 uplink, 스위치 장애, trunk, VLAN 문제 가능성이 높다.

유선은 정상 + 무선만 문제:
AP, 무선 신호, 채널 간섭, 동시 접속자 수 문제 가능성이 높다.

무선 신호는 강한데 느림:
AP uplink, 채널 혼잡, 대역폭 부족, AP 과부하 가능성이 있다.

게이트웨이 ping 실패:
L1/L2, VLAN, ARP, 게이트웨이 IP 오류 가능성이 있다.

게이트웨이 ping 성공 + 외부 IP 실패:
라우터, NAT, WAN, 방화벽, ISP 문제 가능성이 있다.

외부 IP 성공 + 도메인 실패:
DNS 문제 가능성이 높다.

ping은 되는데 특정 서비스 실패:
포트, 방화벽, 서비스 리스닝 문제 가능성이 높다.

특정 시간대에만 느림:
대역폭 부족, 트래픽 폭증, 장비 과부하, ISP 혼잡 가능성이 높다.

packet loss가 게이트웨이부터 발생:
로컬 LAN, Wi-Fi, 케이블, 스위치 문제 가능성이 높다.

packet loss가 외부에서만 발생:
WAN, ISP, 중간 경로 문제 가능성이 있다.

링크 속도가 100Mbps로 잡힘:
케이블, 포트, NIC, 자동 협상 문제 가능성이 있다.

traceroute 첫 홉부터 실패:
클라이언트와 게이트웨이 사이 문제 가능성이 높다.

traceroute 중간 이후 실패:
라우팅, 방화벽, ISP, 중간 장비 문제 가능성이 있다.

특정 VLAN만 문제:
VLAN 설정, trunk, SVI, DHCP relay, ACL 문제 가능성이 있다.

위치에 따라 접속 성공 여부가 다름:
네트워크 정책, DNS, 방화벽, VLAN, 라우팅 차이 가능성이 있다.

패킷 재전송이 많음:
손실, 혼잡, 무선 품질 저하, 장비 부하 가능성이 있다.

ARP 응답이 없음:
L2 연결, VLAN, 게이트웨이, IP 충돌 문제 가능성이 있다.
```

---

## 문제 유형별 해결 방법

### 네트워크가 느릴 때

1. 한 장비만 느린지 여러 장비가 느린지 확인
2. 유선/무선 차이 확인
3. 게이트웨이 ping 지연 확인
4. 외부 IP ping 지연 확인
5. traceroute로 지연 증가 구간 확인
6. 링크 속도 확인
7. 인터페이스 에러 확인
8. 대역폭 사용량 확인
9. 장비 CPU/메모리 확인
10. QoS 또는 정책 확인

명령어:

```bash
ping <gateway_ip>
ping 8.8.8.8
traceroute 8.8.8.8
ip -s link
ethtool <interface>
```

---

### 간헐적으로 끊길 때

1. 끊기는 장비 범위 확인
2. 케이블/포트 변경 테스트
3. Wi-Fi라면 위치와 신호 확인
4. ping을 길게 실행하여 손실 확인
5. 장비 로그에서 link up/down 확인
6. IP 충돌 여부 확인
7. DHCP lease 갱신 시점 확인
8. 스위치 로그/STP 변경 확인
9. 장비 과부하 확인

명령어:

```bash
ping -c 100 <gateway_ip>
ip neigh
dmesg | grep -i link
journalctl -k | grep -i link
```

Windows:

```cmd
ping -n 100 <gateway_ip>
arp -a
```

---

### 특정 위치에서만 안 될 때

1. 같은 PC를 다른 위치에 연결
2. 같은 위치에 다른 PC 연결
3. 케이블 교체
4. 스위치 포트 변경
5. 포트 VLAN 확인
6. AP 신호와 연결 AP 확인
7. 해당 구역 스위치 uplink 확인

판단:

```text
PC를 옮기면 정상:
원래 위치의 케이블/포트/AP 문제 가능성.

다른 PC도 같은 위치에서 문제:
인프라 문제 가능성.

특정 SSID/AP에서만 문제:
AP 또는 무선 정책 문제 가능성.
```

---

### 특정 구간 이후 통신이 실패할 때

1. traceroute 실행
2. 첫 번째 홉 확인
3. 실패 지점이 게이트웨이 이전인지 이후인지 구분
4. 해당 구간의 라우터/방화벽/ISP 확인
5. ACL/NAT/return route 확인
6. ICMP 차단 가능성 고려
7. 실제 서비스 포트 테스트

명령어:

```bash
traceroute <target_ip>
ping <gateway_ip>
nc -vz <target_ip> <port>
```

---

### 유선은 정상인데 Wi-Fi만 문제일 때

1. AP 근처에서 테스트
2. 다른 SSID 테스트
3. 2.4GHz와 5GHz 비교
4. 동시 접속자 수 확인
5. AP uplink 확인
6. DHCP lease 확인
7. 채널 간섭 확인
8. AP 로그 확인

OpenWrt:

```sh
logread | grep hostapd
uci show wireless
```

---

### 링크 속도가 낮게 잡힐 때

1. 케이블 교체
2. 스위치 포트 변경
3. NIC 드라이버 확인
4. 자동 협상 확인
5. 케이블 규격 확인
6. 장비 양쪽이 기가비트를 지원하는지 확인

Linux:

```bash
ethtool <interface>
```

확인:

```text
Speed
Duplex
Auto-negotiation
Link detected
```

---

### 패킷 손실이 있을 때

1. 게이트웨이 ping 손실 확인
2. 외부 IP ping 손실 확인
3. 유선/무선 비교
4. 다른 케이블/포트 테스트
5. 인터페이스 에러 확인
6. traceroute로 손실 구간 추정
7. 장비 부하 확인
8. ISP 문제 가능성 확인

명령어:

```bash
ping -c 100 <gateway_ip>
ping -c 100 8.8.8.8
ip -s link
traceroute 8.8.8.8
```

---

### VLAN 관련 문제가 의심될 때

1. 해당 장비가 어느 VLAN에 속하는지 확인
2. access port VLAN 확인
3. trunk allowed VLAN 확인
4. gateway/SVI 상태 확인
5. DHCP가 해당 VLAN에서 동작하는지 확인
6. VLAN 간 라우팅 확인
7. ACL 확인

점검 항목:

```text
같은 VLAN 내부 통신 가능?
gateway ping 가능?
다른 VLAN 통신 가능?
DHCP lease 정상?
특정 VLAN만 문제?
```

---

### 장비 과부하가 의심될 때

1. 문제가 특정 시간대에 발생하는지 확인
2. 장비 CPU/메모리 사용률 확인
3. 인터페이스 사용률 확인
4. drop/error counter 확인
5. 세션 테이블 사용량 확인
6. 트래픽 상위 사용자 확인
7. 백업/동기화 작업 확인
8. QoS 정책 확인

증상:

```text
특정 시간대 전체 속도 저하
ping 지연 증가
패킷 손실 증가
방화벽 세션 실패
웹 접속 지연
```

---

## 에이전트 응답 전략

네트워크 인프라 문제로 의심될 때 에이전트는 바로 특정 명령어 하나만 제시하지 말고, 먼저 문제 범위를 좁혀야 한다.

우선 물어볼 정보:

```text
1. 한 장비만 문제인지 여러 장비가 문제인지
2. 유선인지 무선인지
3. 특정 위치에서만 발생하는지
4. 특정 시간대에만 발생하는지
5. 같은 LAN 내부 통신은 되는지
6. 기본 게이트웨이 ping은 되는지
7. 8.8.8.8 ping은 되는지
8. 도메인 접속만 안 되는지
9. 특정 서비스만 안 되는지
10. 최근 케이블, 스위치, 공유기, 라우터, VLAN 설정 변경이 있었는지
11. VM, Docker, VPN, OpenWrt, 공유기 환경인지
```

우선 요청할 명령어:

Windows:

```cmd
ipconfig /all
ping <gateway_ip>
ping 8.8.8.8
tracert 8.8.8.8
arp -a
route print
```

Linux:

```bash
ip addr
ip route
ping <gateway_ip>
ping 8.8.8.8
traceroute 8.8.8.8
ip -s link
ip neigh
```

링크 상태 확인:

```bash
ethtool <interface>
```

포트/서비스 분리:

```bash
nc -vz <server_ip> <port>
```

DNS 분리:

```bash
nslookup google.com
```

---

## 에이전트 응답 예시

### 예시 1: 네트워크가 전체적으로 느린 경우

사용자 입력:

```text
사무실 인터넷이 전체적으로 느려
```

에이전트 응답:

```text
사무실 전체가 느리다면 특정 PC 하나의 문제보다는 공유기, 라우터, 방화벽, 스위치 uplink, ISP 회선, 또는 대역폭 부족 문제일 가능성이 있습니다.

먼저 문제가 전체 장비에서 발생하는지, 특정 구역이나 특정 Wi-Fi에서만 발생하는지 확인해야 합니다.

기본 확인 순서는 다음과 같습니다.

Windows:
`ipconfig /all`
`ping <gateway_ip>`
`ping 8.8.8.8`
`tracert 8.8.8.8`

Linux:
`ip addr`
`ip route`
`ping <gateway_ip>`
`ping 8.8.8.8`
`traceroute 8.8.8.8`

게이트웨이 ping부터 지연이 크거나 손실이 있으면 내부 LAN, 스위치, Wi-Fi, 공유기 문제 가능성이 큽니다. 게이트웨이는 빠른데 외부 IP에서만 지연이 크면 WAN, 방화벽, ISP 회선 문제 가능성이 높습니다.
```

---

### 예시 2: 특정 자리에서만 인터넷이 안 되는 경우

사용자 입력:

```text
다른 자리는 되는데 내 자리 랜선만 인터넷이 안 돼
```

에이전트 응답:

```text
특정 자리에서만 문제가 발생한다면 PC 자체보다 해당 자리의 케이블, 벽면 포트, 스위치 포트, VLAN 설정 문제일 가능성이 있습니다.

먼저 같은 PC를 다른 자리의 랜선에 연결했을 때 정상인지 확인하세요. 반대로 다른 PC를 문제 있는 자리의 랜선에 연결했을 때도 문제가 나는지 확인하면 원인을 빠르게 좁힐 수 있습니다.

확인 순서는 다음과 같습니다.

1. 랜 케이블 교체
2. 다른 벽면 포트 또는 스위치 포트 사용
3. `ipconfig /all` 또는 `ip addr`로 IP를 정상적으로 받는지 확인
4. 기본 게이트웨이 ping 확인
5. 해당 포트가 올바른 VLAN에 속하는지 확인

만약 문제 있는 자리에서만 IP를 못 받는다면 케이블, 스위치 포트, VLAN, DHCP 전달 문제를 의심할 수 있습니다.
```

---

### 예시 3: 간헐적으로 끊기는 경우

사용자 입력:

```text
인터넷이 계속 되는 건 아닌데 중간중간 끊겨
```

에이전트 응답:

```text
간헐적 끊김은 케이블 접촉 불량, Wi-Fi 간섭, 스위치 포트 문제, IP 충돌, 장비 과부하, DHCP 갱신 문제 등 여러 원인이 있을 수 있습니다.

먼저 게이트웨이를 대상으로 긴 ping 테스트를 해보세요.

Windows:
`ping -n 100 <gateway_ip>`

Linux:
`ping -c 100 <gateway_ip>`

게이트웨이 ping에서도 손실이 발생하면 내부 네트워크 문제 가능성이 큽니다. 유선이라면 케이블과 스위치 포트를 바꿔보고, 무선이라면 AP 근처에서 테스트해보는 것이 좋습니다.

Linux에서는 링크 이벤트도 확인할 수 있습니다.

`dmesg | grep -i link`
`journalctl -k | grep -i link`

link up/down 로그가 반복된다면 물리 연결이나 NIC 문제 가능성이 있습니다.
```

---

### 예시 4: 특정 구간 이후 traceroute가 멈추는 경우

사용자 입력:

```text
traceroute 해보니까 특정 구간 이후로 별표만 나와
```

에이전트 응답:

```text
traceroute에서 별표가 나온다고 해서 반드시 그 구간이 장애라는 뜻은 아닙니다. 중간 라우터나 방화벽이 ICMP 응답을 차단하면 별표로 보일 수 있습니다.

중요한 것은 실제 목적지 서비스 접속이 되는지와 어느 홉까지 정상적으로 보이는지입니다.

판단 기준은 다음과 같습니다.

1. 첫 번째 홉부터 실패하면 내 PC와 게이트웨이 사이 문제 가능성
2. 게이트웨이까지는 보이고 이후 실패하면 라우터, 방화벽, ISP, NAT 문제 가능성
3. 중간 홉은 별표지만 최종 목적지에 도달하면 정상일 수 있음
4. traceroute 실패와 함께 실제 서비스도 안 되면 해당 경로의 라우팅/방화벽 문제 가능성

추가로 포트 테스트도 해보세요.

`nc -vz <target_ip> <port>`
```

---

### 예시 5: Wi-Fi만 느린 경우

사용자 입력:

```text
유선은 괜찮은데 와이파이만 느려
```

에이전트 응답:

```text
유선은 정상인데 Wi-Fi만 느리다면 인터넷 회선 자체보다는 AP, 무선 신호, 채널 간섭, 동시 접속자 수, AP uplink 문제일 가능성이 높습니다.

먼저 AP 가까이에서 속도와 ping을 비교해보세요. AP 가까이에서는 정상인데 멀어질수록 느리다면 신호 세기나 장애물 문제가 큽니다.

확인할 내용은 다음과 같습니다.

1. 2.4GHz와 5GHz 모두 같은지 확인
2. AP 근처와 먼 위치에서 비교
3. 특정 SSID만 문제인지 확인
4. 동시에 접속한 사용자가 많은지 확인
5. AP의 유선 uplink가 정상인지 확인
6. 게이트웨이 ping에서 손실이 있는지 확인

게이트웨이 ping부터 손실이 있으면 무선 구간 품질 문제 가능성이 큽니다.
```

---

### 예시 6: 링크 속도가 100Mbps로 잡히는 경우

사용자 입력:

```text
기가 인터넷인데 리눅스에서 100Mbps로 잡혀
```

에이전트 응답:

```text
기가비트 환경인데 링크가 100Mbps로 잡힌다면 케이블, 스위치 포트, NIC 자동 협상 문제를 먼저 의심해야 합니다.

Linux에서는 다음 명령어로 링크 상태를 확인하세요.

`ethtool <interface>`

확인할 항목은 다음입니다.

`Speed`
`Duplex`
`Auto-negotiation`
`Link detected`

1Gbps를 기대하는데 `Speed: 100Mb/s`로 나온다면 케이블을 먼저 교체해보는 것이 좋습니다. 특히 케이블 품질이 낮거나 일부 선이 불량이면 링크는 살아도 100Mbps로만 협상될 수 있습니다.

그 다음 스위치 포트 변경, NIC 드라이버 확인, 장비 양쪽의 기가비트 지원 여부를 확인하세요.
```

---

## 주의할 점

네트워크 인프라 문제를 진단할 때 다음을 주의해야 한다.

1. "인터넷이 안 된다"는 말만 듣고 DNS, DHCP, 방화벽 중 하나로 바로 단정하면 안 된다.
2. 인프라 문제는 영향 범위 파악이 가장 중요하다.
3. 한 장비만 문제인지, 여러 장비가 동시에 문제인지 먼저 확인해야 한다.
4. 유선과 무선 문제는 원인 범주가 다르다.
5. ping 성공은 특정 서비스 접속 성공을 의미하지 않는다.
6. ping 실패는 ICMP 차단일 수도 있으므로 단독으로 판단하면 안 된다.
7. traceroute의 별표는 반드시 장애를 의미하지 않는다.
8. 특정 위치에서만 문제라면 케이블, 포트, AP, VLAN 문제를 우선 의심한다.
9. 특정 시간대만 느리면 대역폭 부족, 트래픽 폭증, 장비 과부하 가능성이 있다.
10. 게이트웨이 ping에서 손실이 있으면 내부 네트워크 문제 가능성이 크다.
11. 외부 IP에서만 손실이 있으면 WAN, ISP, 중간 경로 문제 가능성이 있다.
12. 100Mbps로 링크가 잡히면 케이블/포트/자동 협상 문제를 확인한다.
13. VLAN 환경에서는 포트가 올바른 VLAN에 속하는지 확인해야 한다.
14. 스위치 loop는 네트워크 전체 장애를 유발할 수 있다.
15. 무단 공유기나 스위치 연결은 DHCP/Routing/VLAN 문제를 만들 수 있다.
16. IP 충돌은 간헐적 장애를 만들 수 있다.
17. 방화벽이나 보안 장비는 네트워크 위치에 따라 접속 가능 여부를 다르게 만들 수 있다.
18. Wi-Fi 문제는 신호 세기뿐 아니라 간섭, AP uplink, 접속자 수까지 고려해야 한다.
19. MTU 문제는 일반 ping은 되는데 특정 웹/VPN/업로드가 실패할 때 고려한다.
20. 인프라 문제처럼 보여도 최종 원인은 DNS, DHCP, Gateway, Firewall 문서에 있을 수 있다.

---

## 빠른 진단 요약

```text
1. 문제 범위 확인: 한 장비인지, 여러 장비인지, 특정 위치인지
2. 유선/무선 여부 확인
3. 최근 변경 사항 확인: 케이블, 스위치, 라우터, VLAN, 방화벽, AP
4. 물리 연결 확인: 링크 LED, 케이블, 포트, NIC
5. IP 설정 확인: ipconfig /all 또는 ip addr
6. 기본 게이트웨이 확인
7. ping <gateway_ip>로 내부 연결 확인
8. ping 8.8.8.8로 외부 IP 연결 확인
9. nslookup으로 DNS 문제 분리
10. nc/Test-NetConnection으로 포트 문제 분리
11. traceroute/tracert로 끊기는 구간 확인
12. ip -s link 또는 Get-NetAdapterStatistics로 에러 확인
13. ethtool로 링크 속도/duplex 확인
14. 위치별/장비별 비교 테스트
15. 필요 시 Wireshark/tcpdump로 패킷 확인
```

---

## 핵심 키워드

Network Infrastructure, Network Infrastructure Troubleshooting, 네트워크 인프라, 네트워크 느림, 인터넷 느림, 간헐적 끊김, 특정 위치에서만 안 됨, 특정 구간 통신 실패, 같은 서비스 위치별 접속 차이, 케이블 문제, 스위치 문제, 라우터 문제, AP 문제, Wi-Fi 문제, 무선 간섭, 링크 속도, 100Mbps, 1Gbps, duplex mismatch, auto negotiation, ethtool, ip -s link, Get-NetAdapter, Get-NetAdapterStatistics, ping packet loss, packet loss, latency, jitter, traceroute, tracert, tracepath, gateway ping, ip route, route print, ARP, ip neigh, arp -a, VLAN, trunk, access port, SVI, STP, loop, broadcast storm, MAC address table, switch uplink, router, L3 switch, firewall, NAT, QoS, bandwidth bottleneck, congestion, interface errors, RX errors, TX errors, dropped packets, carrier errors, Wireshark, tcpdump, DHCP, DNS, Gateway, Routing, Firewall, MTU, Path MTU Discovery, VPN, OpenWrt, uci show network, uci show wireless, logread, ifstatus wan, ifstatus lan.