prompts = [
    {
        "title": "LLM 프롬프트 엔지니어링 글 작성",
        "content": (
            "LLM 프롬프트 엔지니어링의 핵심 원칙과 실전 활용법을 "
            "초보자도 이해하기 쉽게 설명하는 글을 작성해 주세요."
        ),
        "category": "텍스트 생성",
        "favorite": False,
    },
    {
        "title": "EchoLens 광고 이미지 제작",
        "content": (
            "EchoLens의 혁신적인 브랜드 이미지를 강조하는 미래지향적 광고 이미지를 "
            "제작해 주세요. 제품이 중심에 보이고 세련된 조명을 사용해 주세요."
        ),
        "category": "이미지 생성",
        "favorite": False,
    },
    {
        "title": "AI 뉴스 자동화",
        "content": (
            "매일 최신 AI 뉴스를 수집하고 핵심 내용을 요약한 뒤, "
            "주제별로 분류하여 보고서를 작성하는 작업을 자동화해 주세요."
        ),
        "category": "자동화",
        "favorite": False,
    },
]


def show_menu():
    print("\n=== 프롬프트 관리자 ===")
    print("1. 프롬프트 추가")
    print("2. 프롬프트 목록")
    print("3. 카테고리별 조회")
    print("4. 프롬프트 검색")
    print("5. 프롬프트 상세 보기")
    print("6. 즐겨찾기 관리")
    print("7. 즐겨찾기 목록")
    print("0. 종료")


def add_prompt():
    while True:
        title = input("제목을 입력하세요: ").strip()
        if title:
            break
        print("제목을 입력해주세요.")

    while True:
        content = input("내용을 입력하세요: ").strip()
        if content:
            break
        print("내용을 입력해주세요.")

    categories = [
        "텍스트 생성",
        "이미지 생성",
        "영상 생성",
        "페르소나",
        "자동화",
        "기타",
    ]

    while True:
        print("\n카테고리를 선택하세요.")
        for index, category in enumerate(categories, start=1):
            print(f"{index}. {category}")

        category_choice = input("카테고리 번호를 입력하세요: ").strip()
        if category_choice in ["1", "2", "3", "4", "5", "6"]:
            category = categories[int(category_choice) - 1]
            break
        print("올바른 카테고리 번호를 입력해주세요.")

    prompts.append(
        {
            "title": title,
            "content": content,
            "category": category,
            "favorite": False,
        }
    )
    print("프롬프트가 추가되었습니다.")


def show_list():
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return

    for index, prompt in enumerate(prompts, start=1):
        favorite_mark = "O" if prompt["favorite"] else "X"
        print(
            f"{index}. {prompt['title']} | "
            f"카테고리: {prompt['category']} | 즐겨찾기: {favorite_mark}"
        )


def category_list():
    if not prompts:
        print("등록된 프롬프트가 없습니다.")
        return

    categories = []
    for prompt in prompts:
        if prompt["category"] not in categories:
            categories.append(prompt["category"])

    while True:
        print("\n=== 카테고리 목록 ===")
        for index, category in enumerate(categories, start=1):
            print(f"{index}. {category}")

        category_choice = input("카테고리 번호를 입력하세요: ").strip()
        if category_choice.isdigit():
            category_index = int(category_choice) - 1
            if 0 <= category_index < len(categories):
                selected_category = categories[category_index]
                break
        print("올바른 카테고리 번호를 입력해주세요.")

    matching_prompts = [
        (index, prompt)
        for index, prompt in enumerate(prompts, start=1)
        if prompt["category"] == selected_category
    ]

    if not matching_prompts:
        print("해당 카테고리에 등록된 프롬프트가 없습니다.")
        return

    for index, prompt in matching_prompts:
        favorite_mark = "O" if prompt["favorite"] else "X"
        print(
            f"{index}. {prompt['title']} | "
            f"카테고리: {prompt['category']} | 즐겨찾기: {favorite_mark}"
        )


def get_menu_choice():
    return input("메뉴 번호를 입력하세요: ").strip()


def run_menu_choice(choice):
    if choice == "0":
        print("프로그램을 종료합니다.")
        return False
    if choice == "1":
        add_prompt()
    elif choice == "2":
        show_list()
    elif choice == "3":
        category_list()
    elif choice in ["4", "5", "6", "7"]:
        print("아직 구현되지 않은 기능입니다.")
    else:
        print("올바른 메뉴 번호를 입력해주세요.")
    return True


def main():
    while True:
        show_menu()
        choice = get_menu_choice()
        if not run_menu_choice(choice):
            break


if __name__ == "__main__":
    main()
