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
            throw new Error(`HTTP ${response.status}`);
        }

        // 브라우저 정책상 window.close()가 실패할 수 있음
        window.close();

        // 닫히지 않은 경우 표시할 화면
        document.body.innerHTML = `
            <div class="shutdown-screen">
                <h1>Daily Board가 종료되었습니다.</h1>
                <p>이 페이지를 닫아도 됩니다.</p>
            </div>
        `;

    } catch (error) {
        console.error("서버 종료 요청 실패:", error);

        window.alert(
            "서버를 종료하지 못했습니다."
        );
    }
}

export function initializeShutdownButton() {
    const button = document.getElementById(
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