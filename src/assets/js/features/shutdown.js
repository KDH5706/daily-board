async function shutdownServer() {
    const confirmed = window.confirm(
        "Daily Board 서버를 종료하시겠습니까?"
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch("/__shutdown__", {
            method: "POST",
            cache: "no-store",
        });

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        // 서버가 응답을 반환한 뒤 현재 페이지 닫기
        window.close();

    } catch (error) {
        console.error(
            "서버 종료 요청 실패:",
            error
        );
    }
}

export function initializeShutdownButton() {
    const button =
        document.getElementById(
            "shutdownServerButton"
        );

    if (!button) {
        return;
    }

    button.addEventListener(
        "click",
        shutdownServer
    );
}