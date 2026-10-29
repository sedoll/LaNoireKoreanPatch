# L.A. 누아르 한국어 번역 가이드

배경: 1947년 로스앤젤레스. 해병대 출신 신참 경찰 콜 펠프스가 순찰 → 교통과 → 강력과 → 풍속과 → 방화과를 거치며 사건을 수사하는 하드보일드 누아르. 문체는 1940년대 형사물 느낌으로, 자연스럽고 간결한 한국어 구어체로 옮긴다. 직역 투(“그것은 ~이다”)는 피한다.

## 반드시 지킬 규칙

1. **태그는 한 글자도 바꾸지 않는다.** `[2s]`, `[0.5s]`, `[BR]`, `[GAP]`, `[BLANK]`, `[ACCEPT|PCSELECT]`, `[LEFTSTICK|MOVEMENTKEYS]`, `[R*]` 등 대괄호로 된 것은 전부 원문과 같은 개수, 같은 철자로 남긴다. 번역문에 새 대괄호를 만들지 않는다.
2. **자막 타이밍 태그(`[숫자s]`)는 문장 구간의 경계다.** 원문에서 태그 사이에 있던 내용은 번역문에서도 같은 태그 사이에 들어가야 한다. 구간을 합치거나 순서를 바꾸지 않는다. 예:
   `[2s]Sexual assault. [2.6s]Look, I was lying there on the sidewalk.` → `[2s]성폭행이요. [2.6s]이봐요, 난 인도에 쓰러져 있었다고요.`
3. 태그 바로 앞뒤의 공백도 원문과 비슷하게 유지한다.
4. `%s`, `%d`, `µ`, URL, 이메일, 차량 번호(예: 11K), 무전 호출부호(KGPL)는 그대로 둔다.
5. 원문 끝의 공백은 신경 쓰지 않아도 된다.
6. 욕설과 시대상 표현은 순화하지 말고 자연스러운 한국어 욕설/표현으로 옮긴다.
7. 줄바꿈 문자(실제 개행)는 넣지 않는다.

## 말투

- **콜 펠프스**: 딱딱하고 원칙적인 성격. 상관에게 하십시오체. 증인·용의자에게 기본은 존댓말(하십시오체/해요체), 몰아붙일 때만 반말 가능. 파트너에게는 해요체.
- **파트너들(러스티 갤러웨이, 로이 얼, 허셜 빅스, 스테판 베코스키, 랄프 던)**: 펠프스보다 고참이며 펠프스에게 반말.
- **상관(경감·경위·국장 등)**: 부하에게 반말.
- **증인·용의자**: 성격과 상황에 맞게. 점잖은 시민은 존댓말, 깡패·적대적인 인물은 반말·비속어.
- **무전(dispatch)**: 군더더기 없는 무전 말투(“알았다”, “전 차량에 알린다”).
- 같은 두 인물 사이의 말투는 일관되게 유지한다.

## UI·튜토리얼·단서 문구

- 메뉴/버튼 라벨은 짧게(“계속”, “불러오기”, “설정”). 영어 원문이 대문자여도 한국어는 그냥 쓴다.
- 튜토리얼 문장은 “~하세요”체.
- 수첩 항목(장소, 관련 인물, 단서 설명)은 명사형/개조식(“~한 흔적”, “피해자의 남편”).
- 주소: `650 North Kingsley Drive` → `노스 킹슬리 드라이브 650번지`, `Corner of Third and Hill` → `서드와 힐 교차로`.

## 용어집 (반드시 이 표기를 사용)

| 영어 | 한국어 |
|---|---|
| Cole Phelps | 콜 펠프스 |
| Roy Earle | 로이 얼 |
| Rusty Galloway (Finbarr Galloway) | 러스티 갤러웨이 (핀바 갤러웨이) |
| Stefan Bekowsky | 스테판 베코스키 |
| Herschel Biggs | 허셜 빅스 |
| Jack Kelso | 잭 켈소 |
| Ralph Dunn | 랄프 던 |
| Marie Phelps | 마리 펠프스 |
| Elsa Lichtmann | 엘자 리히트만 |
| Courtney Sheldon | 코트니 셸던 |
| Malcolm Carruthers | 맬컴 캐러더스 |
| James Donnelly | 제임스 도널리 |
| Gordon Pinker | 고든 핑커 |
| Leland Monroe | 릴런드 먼로 |
| Harlan Fontaine | 할런 퐁텐 |
| Mickey Cohen | 미키 코언 |
| Ira Hogeboom | 아이라 호지붐 |
| Hugo Moller | 휴고 몰러 |
| Curtis Benson | 커티스 벤슨 |
| William Worrell | 윌리엄 워렐 |
| Captain Leary | 리어리 경감 |
| Captain McKelty | 매켈티 경감 |
| Lieutenant Goodwin | 굿윈 경위 |
| Lieutenant Archer | 아처 경위 |
| Chief Worrell | 워렐 국장 |
| Mayor Fletcher Bowron | 플레처 보런 시장 |
| Dispatch | 통신 본부 (무전에서는 “본부”) |
| LAPD | LA 경찰국 (대사에서는 “LAPD”도 가능) |
| Patrol | 순찰과 |
| Traffic | 교통과 |
| Homicide | 강력과 |
| Vice | 풍속과 |
| Arson | 방화과 |
| Ad Vice | 풍속과 |
| Captain / Lieutenant / Sergeant / Detective / Patrolman / Officer | 경감 / 경위 / 경사 / 형사 / 순경 / 경관 |
| Chief of Police | 경찰국장 |
| Coroner | 검시관 |
| D.A. (District Attorney) | 지방 검사 |
| Code Four | 코드 4 |
| APB | 지명수배 |
| Black Dahlia | 블랙 달리아 |
| Suburban Redevelopment Fund | 교외 재개발 기금 |
| Elysian Fields Development | 엘리시안 필즈 개발 |
| Sixth Marine Division | 제6해병사단 |
| Okinawa | 오키나와 |
| Truth / Doubt / Lie | 진실 / 의심 / 거짓 |
| Intuition / Intuition Point | 직감 / 직감 포인트 |
| Notebook | 수첩 |
| Clue | 단서 |
| Persons of Interest | 관련 인물 |
| Locations | 장소 |
| Questions | 질문 |
| Case Closed | 사건 종결 |
| Street Crime | 거리 범죄 |
| Landmark | 랜드마크 |
| Film Reel | 필름 릴 |
| Hidden Vehicle | 숨겨진 차량 |
| Golden Badge | 금 배지 |
| Partner | 파트너 |
| Central Division / Central Station | 센트럴 분서 / 센트럴 경찰서 |
| Wilshire / Hollywood / Hollenbeck / University (division) | 윌셔 / 할리우드 / 홀렌벡 / 유니버시티 (분서) |
| Main Street / Sunset Boulevard / Wilshire Boulevard | 메인 스트리트 / 선셋 대로 / 윌셔 대로 |
| Street / Avenue / Boulevard / Drive / Place / Road | 스트리트 / 애비뉴 / 대로 / 드라이브 / 플레이스 / 로드 |

그 밖의 인명·지명은 국립국어원 외래어 표기법에 따라 음역하고, 같은 배치 안에서는 한 가지 표기로 통일한다. 실존 영화·책·노래 제목은 통용되는 한국어 제목이 있으면 그것을 쓴다.
