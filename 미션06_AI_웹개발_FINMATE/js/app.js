// ==========================================================
// FINMATE AI
// Frontend JavaScript - Final Version
// ==========================================================


// ==========================================================
// 1. HTML 요소 가져오기
// ==========================================================

const analysisForm = document.getElementById("analysisForm");
const companyInput = document.getElementById("companyInput");
const analyzeButton = document.getElementById("analyzeButton");
const statusMessage = document.getElementById("statusMessage");
const analysisResult = document.getElementById("analysisResult");
const themeToggle = document.getElementById("themeToggle");


// ==========================================================
// 2. 다크 모드
// ==========================================================

if (themeToggle) {
    themeToggle.addEventListener("click", () => {

        document.body.classList.toggle("dark");

        if (document.body.classList.contains("dark")) {
            themeToggle.textContent = "☀️";
        } else {
            themeToggle.textContent = "🌙";
        }

    });
}


// ==========================================================
// 3. 페이지 내 메뉴 이동
// ==========================================================

document.querySelectorAll('a[href^="#"]').forEach((link) => {

    link.addEventListener("click", (event) => {

        const targetId = link.getAttribute("href");

        if (!targetId || targetId === "#") {
            return;
        }

        const targetElement = document.querySelector(targetId);

        if (!targetElement) {
            return;
        }

        event.preventDefault();

        targetElement.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

        history.replaceState(
            null,
            "",
            targetId
        );

    });

});


// ==========================================================
// 4. 상태 메시지 표시
// ==========================================================

function showStatus(message, type = "info") {

    if (!statusMessage) {
        return;
    }

    statusMessage.textContent = message;

    statusMessage.classList.remove(
        "status-error",
        "status-success",
        "status-loading",
        "status-info"
    );

    if (type === "error") {
        statusMessage.classList.add("status-error");
    } else if (type === "success") {
        statusMessage.classList.add("status-success");
    } else if (type === "loading") {
        statusMessage.classList.add("status-loading");
    } else {
        statusMessage.classList.add("status-info");
    }

}


// ==========================================================
// 5. HTML 특수문자 안전 처리
// ==========================================================

function escapeHtml(text) {

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


// ==========================================================
// 6. Gemini 결과 간단 Markdown 변환
// ==========================================================

function formatAnalysisText(text) {

    // AI 응답을 그대로 innerHTML에 넣지 않고
    // 먼저 HTML 특수문자를 안전하게 처리한다.
    let formattedText = escapeHtml(text);


    // **굵은 글씨**
    formattedText = formattedText.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    // 줄바꿈
    formattedText = formattedText.replace(
        /\r?\n/g,
        "<br>"
    );


    return formattedText;

}


// ==========================================================
// 7. AI 분석 결과 표시
// ==========================================================

function showResult(text) {

    if (!analysisResult) {
        return;
    }

    analysisResult.innerHTML = "";

    const resultText = document.createElement("div");

    resultText.className = "result-text";

    resultText.innerHTML = formatAnalysisText(text);

    analysisResult.appendChild(resultText);

}


// ==========================================================
// 8. 로딩 화면 표시
// ==========================================================

function showLoadingResult() {

    if (!analysisResult) {
        return;
    }

    analysisResult.innerHTML = `
        <p class="empty-result">
            AI가 기업 정보를 분석하고 있습니다.
            잠시만 기다려주세요.
        </p>
    `;

}


// ==========================================================
// 9. 오류 화면 표시
// ==========================================================

function showErrorResult() {

    if (!analysisResult) {
        return;
    }

    analysisResult.innerHTML = `
        <p class="empty-result">
            분석 결과를 불러오지 못했습니다.
        </p>
    `;

}


// ==========================================================
// 10. AI 기업 분석
// ==========================================================

if (
    analysisForm &&
    companyInput &&
    analyzeButton
) {

    analysisForm.addEventListener(
        "submit",
        async (event) => {

            // form 제출 시 페이지 새로고침 방지
            event.preventDefault();


            // --------------------------------------------------
            // 사용자 입력값
            // --------------------------------------------------

            const company = companyInput.value.trim();


            // --------------------------------------------------
            // 빈 입력 검사
            // --------------------------------------------------

            if (!company) {

                showStatus(
                    "분석할 기업명을 입력해주세요.",
                    "error"
                );

                companyInput.focus();

                return;
            }


            // --------------------------------------------------
            // 지나치게 긴 입력 검사
            // --------------------------------------------------

            if (company.length > 100) {

                showStatus(
                    "기업명은 100자 이하로 입력해주세요.",
                    "error"
                );

                companyInput.focus();

                return;
            }


            // --------------------------------------------------
            // 분석 시작 상태
            // --------------------------------------------------

            showStatus(
                "AI가 기업 정보를 분석하고 있습니다...",
                "loading"
            );

            showLoadingResult();


            // 중복 API 요청 방지
            analyzeButton.disabled = true;

            analyzeButton.textContent = "분석 중...";


            try {

                // ==================================================
                // Python Vercel Serverless Function 호출
                // ==================================================

                const response = await fetch(
                    "/api/analyze",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type": "application/json"
                        },

                        body: JSON.stringify({
                            company: company
                        })
                    }
                );


                // ==================================================
                // 서버 응답 JSON 처리
                // ==================================================

                let data;

                try {

                    data = await response.json();

                } catch (jsonError) {

                    console.error(
                        "JSON 응답 처리 오류:",
                        jsonError
                    );

                    throw new Error(
                        "INVALID_SERVER_RESPONSE"
                    );

                }


                // ==================================================
                // HTTP 오류 처리
                // ==================================================

                if (!response.ok) {

                    console.error(
                        "API HTTP 오류:",
                        response.status,
                        data
                    );


                    if (
                        response.status === 401 ||
                        response.status === 403
                    ) {

                        throw new Error(
                            "AUTH_ERROR"
                        );

                    }


                    if (response.status === 429) {

                        throw new Error(
                            "RATE_LIMIT"
                        );

                    }


                    if (response.status === 504) {

                        throw new Error(
                            "TIMEOUT"
                        );

                    }


                    if (response.status >= 500) {

                        throw new Error(
                            "SERVER_ERROR"
                        );

                    }


                    throw new Error(
                        "API_ERROR"
                    );

                }


                // ==================================================
                // AI 결과 확인
                // ==================================================

                if (
                    !data.analysis ||
                    !String(data.analysis).trim()
                ) {

                    throw new Error(
                        "EMPTY_RESULT"
                    );

                }


                // ==================================================
                // AI 분석 결과 화면 출력
                // ==================================================

                showResult(
                    data.analysis
                );


                showStatus(
                    `${company} 분석이 완료되었습니다.`,
                    "success"
                );

            } catch (error) {

                // ==================================================
                // 개발자 확인용 오류 로그
                // ==================================================

                console.error(
                    "FINMATE AI 분석 오류:",
                    error
                );


                // ==================================================
                // 사용자용 오류 메시지
                //
                // 중요:
                // Failed to fetch 등의 기술적인 영어 오류를
                // 사용자 화면에 직접 표시하지 않는다.
                // ==================================================

                let userMessage =
                    "AI 분석 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요.";


                // 인증 오류
                if (error.message === "AUTH_ERROR") {

                    userMessage =
                        "AI 서비스 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.";

                }


                // 사용량 제한
                else if (error.message === "RATE_LIMIT") {

                    userMessage =
                        "현재 AI 요청이 많습니다. 잠시 후 다시 시도해주세요.";

                }


                // 응답 지연
                else if (error.message === "TIMEOUT") {

                    userMessage =
                        "AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.";

                }


                // 서버 오류
                else if (error.message === "SERVER_ERROR") {

                    userMessage =
                        "AI 서버에서 문제가 발생했습니다. 잠시 후 다시 시도해주세요.";

                }


                // AI 결과 없음
                else if (error.message === "EMPTY_RESULT") {

                    userMessage =
                        "AI 분석 결과를 받아오지 못했습니다. 다시 시도해주세요.";

                }


                // JSON 오류
                else if (
                    error.message ===
                    "INVALID_SERVER_RESPONSE"
                ) {

                    userMessage =
                        "서버 응답을 처리하지 못했습니다. 잠시 후 다시 시도해주세요.";

                }


                // 네트워크가 끊긴 경우
                // fetch 자체 실패 역시 여기로 들어온다.
                else if (
                    error instanceof TypeError ||
                    error.message === "Failed to fetch"
                ) {

                    userMessage =
                        "네트워크 연결 또는 AI 서비스에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.";

                }


                // ==================================================
                // 사용자에게 친화적인 오류 안내
                // ==================================================

                showStatus(
                    userMessage,
                    "error"
                );


                showErrorResult();

            } finally {

                // ==================================================
                // 버튼 원상 복구
                // ==================================================

                analyzeButton.disabled = false;

                analyzeButton.textContent = "AI 분석";

            }

        }
    );

}


// ==========================================================
// 11. 페이지 최초 실행 시 hash 위치 이동
// ==========================================================

window.addEventListener("load", () => {

    if (!window.location.hash) {
        return;
    }

    const targetElement = document.querySelector(
        window.location.hash
    );

    if (!targetElement) {
        return;
    }

    setTimeout(() => {

        targetElement.scrollIntoView({
            behavior: "auto",
            block: "start"
        });

    }, 50);

});