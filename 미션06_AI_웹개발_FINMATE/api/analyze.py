import json
import os
import urllib.request
import urllib.error

from http.server import BaseHTTPRequestHandler


# =========================================================
# FINMATE AI - Vercel Serverless Function
# =========================================================

MODEL_NAME = "gemini-3.6-flash"


class handler(BaseHTTPRequestHandler):

    # -----------------------------------------------------
    # JSON 응답 함수
    # -----------------------------------------------------
    def send_json(self, status_code, data):

        response_body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(response_body))
        )

        self.end_headers()

        self.wfile.write(response_body)


    # -----------------------------------------------------
    # POST 요청 처리
    # -----------------------------------------------------
    def do_POST(self):

        try:

            # =================================================
            # 1. Gemini API Key 확인
            # =================================================

            api_key = os.environ.get(
                "GEMINI_API_KEY"
            )

            if not api_key:

                print(
                    "ERROR: GEMINI_API_KEY is not configured."
                )

                self.send_json(
                    500,
                    {
                        "error":
                        "서버에 Gemini API Key가 설정되지 않았습니다."
                    }
                )

                return


            # =================================================
            # 2. 사용자 요청 읽기
            # =================================================

            try:

                content_length = int(
                    self.headers.get(
                        "Content-Length",
                        0
                    )
                )

                request_body = self.rfile.read(
                    content_length
                )

                data = json.loads(
                    request_body.decode("utf-8")
                )

            except (
                ValueError,
                json.JSONDecodeError
            ):

                self.send_json(
                    400,
                    {
                        "error":
                        "잘못된 요청 형식입니다."
                    }
                )

                return


            # =================================================
            # 3. 기업명 가져오기
            # =================================================

            company = str(
                data.get(
                    "company",
                    ""
                )
            ).strip()


            # 빈 입력 검사
            if not company:

                self.send_json(
                    400,
                    {
                        "error":
                        "분석할 기업명을 입력해주세요."
                    }
                )

                return


            # 지나치게 긴 입력 차단
            if len(company) > 100:

                self.send_json(
                    400,
                    {
                        "error":
                        "기업명은 100자 이하로 입력해주세요."
                    }
                )

                return


            # =================================================
            # 4. Gemini에게 전달할 Prompt
            # =================================================

            prompt = f"""
당신은 투자 초보자를 위한 금융 교육 도우미입니다.

다음 기업을 투자 초보자도 이해할 수 있도록
쉽고 객관적으로 설명해주세요.

기업명:
{company}


반드시 다음 구조를 사용해주세요.


[기업 소개]

이 기업이 어떤 회사인지
2~3문장으로 쉽게 설명해주세요.


[주요 사업]

기업이 어떤 제품이나 서비스를 통해
사업을 하는지 설명해주세요.


[강점]

이 기업이 가지고 있는 대표적인 경쟁력이나
장점을 2~3개 설명해주세요.


[위험 요소]

이 기업을 공부할 때 알아두어야 할
대표적인 위험 요소를 2~3개 설명해주세요.


[초보자 한줄 정리]

기업의 특징을 투자 초보자가 이해할 수 있도록
한 문장으로 정리해주세요.


중요한 규칙:

1. 어려운 금융 용어는 최대한 쉽게 설명하세요.
2. 특정 주식의 매수 또는 매도를 권유하지 마세요.
3. 투자 수익을 보장하는 표현을 사용하지 마세요.
4. 최신 주가나 실시간 재무정보를 알고 있다고 가정하지 마세요.
5. 확인되지 않은 숫자를 만들어내지 마세요.
6. 투자 학습 및 정보 제공 목적의 설명만 제공하세요.
7. 한국어로 답변하세요.
"""


            # =================================================
            # 5. Gemini API URL
            # =================================================

            url = (
                "https://generativelanguage.googleapis.com/"
                f"v1beta/models/{MODEL_NAME}:generateContent"
            )


            # =================================================
            # 6. Gemini 요청 데이터
            # =================================================

            payload = {

                "contents": [

                    {

                        "parts": [

                            {
                                "text": prompt
                            }

                        ]

                    }

                ]

            }


            request_data = json.dumps(
                payload,
                ensure_ascii=False
            ).encode("utf-8")


            # =================================================
            # 7. HTTP POST 요청 생성
            # =================================================

            request = urllib.request.Request(

                url,

                data=request_data,

                headers={

                    "Content-Type":
                    "application/json",

                    "x-goog-api-key":
                    api_key

                },

                method="POST"

            )


            # =================================================
            # 8. Gemini API 호출
            # =================================================

            try:

                print(
                    f"Gemini request: model={MODEL_NAME}"
                )

                with urllib.request.urlopen(
                    request,
                    timeout=30
                ) as response:

                    response_text = (
                        response
                        .read()
                        .decode("utf-8")
                    )

                    result = json.loads(
                        response_text
                    )


            # ---------------------------------------------
            # Gemini HTTP 오류
            # ---------------------------------------------

            except urllib.error.HTTPError as error:

                print(
                    "Gemini HTTP Error:",
                    error.code
                )

                # API Key 값은 절대 출력하지 않음

                if error.code in (
                    401,
                    403
                ):

                    message = (
                        "AI API 인증에 실패했습니다."
                    )

                elif error.code == 404:

                    message = (
                        "현재 Gemini 모델을 사용할 수 없습니다."
                    )

                elif error.code == 429:

                    message = (
                        "AI API 사용량 한도에 도달했습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                elif error.code >= 500:

                    message = (
                        "AI 서버가 일시적으로 응답하지 않습니다. "
                        "잠시 후 다시 시도해주세요."
                    )

                else:

                    message = (
                        "AI 서비스 요청 중 오류가 발생했습니다."
                    )


                self.send_json(
                    502,
                    {
                        "error": message
                    }
                )

                return


            # ---------------------------------------------
            # 네트워크 오류
            # ---------------------------------------------

            except urllib.error.URLError as error:

                print(
                    "Gemini Network Error:",
                    str(error.reason)
                )

                self.send_json(
                    503,
                    {
                        "error":
                        "AI 서비스에 연결할 수 없습니다."
                    }
                )

                return


            # ---------------------------------------------
            # 타임아웃
            # ---------------------------------------------

            except TimeoutError:

                print(
                    "Gemini request timeout."
                )

                self.send_json(
                    504,
                    {
                        "error":
                        "AI 응답이 지연되고 있습니다. "
                        "잠시 후 다시 시도해주세요."
                    }
                )

                return


            # =================================================
            # 9. Gemini 응답에서 텍스트 추출
            # =================================================

            try:

                candidates = result.get(
                    "candidates",
                    []
                )

                if not candidates:

                    raise ValueError(
                        "No candidates returned."
                    )


                content = candidates[0].get(
                    "content",
                    {}
                )


                parts = content.get(
                    "parts",
                    []
                )


                if not parts:

                    raise ValueError(
                        "No response parts returned."
                    )


                analysis_parts = []


                for part in parts:

                    text = part.get(
                        "text"
                    )

                    if text:

                        analysis_parts.append(
                            text
                        )


                analysis = "\n".join(
                    analysis_parts
                ).strip()


                if not analysis:

                    raise ValueError(
                        "Empty Gemini response."
                    )


            except (
                KeyError,
                IndexError,
                TypeError,
                ValueError
            ) as error:

                print(
                    "Gemini response parsing error:",
                    str(error)
                )

                self.send_json(
                    502,
                    {
                        "error":
                        "AI 분석 결과를 처리할 수 없습니다."
                    }
                )

                return


            # =================================================
            # 10. 정상 결과 반환
            # =================================================

            print(
                f"FINMATE analysis completed: {company}"
            )


            self.send_json(

                200,

                {

                    "company":
                    company,

                    "analysis":
                    analysis,

                    "model":
                    MODEL_NAME

                }

            )


        # =====================================================
        # 예상하지 못한 서버 오류
        # =====================================================

        except Exception as error:

            print(
                "FINMATE Server Error:",
                type(error).__name__,
                str(error)
            )

            self.send_json(
                500,
                {
                    "error":
                    "서버에서 오류가 발생했습니다."
                }
            )