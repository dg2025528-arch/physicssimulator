#!/usr/bin/env python3
"""index.html (v1.4.2) -> index_v1.4.3.html
사용법:  python patch_v143.py index.html
각 수정 지점을 못 찾으면 파일을 만들지 않고 멈춥니다."""
import re, sys

src = sys.argv[1] if len(sys.argv) > 1 else "index.html"
s = open(src, encoding="utf-8").read()

def sub(pattern, repl, label, flags=re.S):
    global s
    s, n = re.subn(pattern, lambda m: repl(m) if callable(repl) else repl, s, count=1, flags=flags)
    if n != 1:
        sys.exit(f"[실패] 수정 지점을 찾지 못했습니다: {label}")

# 1) 버전
sub(r'<span class="version-badge">v1\.4\.2</span>', '<span class="version-badge">v1.4.3</span>', "version badge")
sub(r'인터랙티브 물리 실험실 · v1\.4\.2', '인터랙티브 물리 실험실 · v1.4.3', "header version")

# 2) 상수/함수
sub(r'let escapeInitialEnergy = null;',
    '''let escapeInitialEnergy = null;

    // 탈출 경계: 행성 중심에서 R × 이 값 만큼 떨어진 거리
    const ESCAPE_BOUNDARY_FACTOR = 2;

    // 경계를 이미 넘었는지 (판정 중복 방지)
    let escapeBoundaryCrossed = false;

    function escapeBoundaryRadius() {
      return (
        Math.max(numberValue(planetRadiusInput, 35), 1) *
        ESCAPE_BOUNDARY_FACTOR
      );
    }''', "constants")

# 3) resetSimulation 초기화
sub(r'\n  escapeInitialEnergy = null;',
    '\n  escapeInitialEnergy = null;\n  escapeBoundaryCrossed = false;', "reset")

# 4) autoFitEscapeZoom 교체
sub(r'function autoFitEscapeZoom\(\) \{.*?(?=\s*function setZoom)',
    '''function autoFitEscapeZoom() {

      const boundaryRadius = escapeBoundaryRadius();

      const baseScale =
        Math.max(5, simulation.clientWidth / 80);

      const desiredScreenRadius =
        Math.min(
          simulation.clientWidth,
          simulation.clientHeight
        ) * 0.44;

      return Math.min(
        Math.max(
          desiredScreenRadius / (boundaryRadius * baseScale),
          MIN_ZOOM
        ),
        MAX_ZOOM
      );
    }
''', "autoFitEscapeZoom")

# 5) 경계 판정 (update의 탈출 분기)
sub(r'/\*\s*역학적 에너지에 따른\s*실시간 상태 표시\s*\*/',
    '''/*
          탈출 경계 판정: 경계를 넘는 순간의 E로 성공 여부를 가린다.
        */

        if (running) {

          const distanceNow = Math.hypot(x, y);

          if (distanceNow < escapeBoundaryRadius()) {

            escapeBoundaryCrossed = false;

          } else if (!escapeBoundaryCrossed) {

            escapeBoundaryCrossed = true;

            const energyAtBoundary =
              computeEscapeMechanicalEnergy();

            if (energyAtBoundary > -ENERGY_EPSILON) {

              running = false;

              playPauseButton.textContent = "▶ 재생";

              message.textContent =
                "탈출 성공! 물체가 탈출 경계(2R)를 넘었습니다.";

            } else {

              message.textContent =
                "탈출 경계를 넘었지만 E < 0 이라 중력에 묶여 있습니다. 다시 돌아올 수 있어요.";
            }
          }
        }


        /*
          역학적 에너지에 따른
          실시간 상태 표시
        */''', "boundary check")

# 6) draw: 반투명 대기권
sub(r'/\*\s*행성 글로우\s*\*/',
    '''/*
          탈출 경계 (반투명 대기권)
        */

        const boundaryTop =
          worldToScreen(0, escapeBoundaryRadius());

        const boundaryPx =
          Math.abs(boundaryTop.y - center.y);

        const atmosphere =
          context.createRadialGradient(
            center.x, center.y, displayRadius,
            center.x, center.y, boundaryPx
          );

        atmosphere.addColorStop(0,   "rgba(120,200,255,0.28)");
        atmosphere.addColorStop(0.5, "rgba(120,200,255,0.10)");
        atmosphere.addColorStop(1,   "rgba(120,200,255,0.03)");

        context.beginPath();
        context.arc(center.x, center.y, boundaryPx, 0, Math.PI * 2);
        context.fillStyle = atmosphere;
        context.fill();

        context.save();
        context.setLineDash([8, 6]);
        context.strokeStyle = "rgba(131,223,255,0.75)";
        context.lineWidth = 1.5;
        context.stroke();
        context.restore();

        context.fillStyle = "rgba(131,223,255,0.9)";
        context.font = "12px sans-serif";
        context.textAlign = "center";
        context.fillText(
          "탈출 경계 (r = 2R)",
          center.x,
          center.y - boundaryPx + 18
        );
        context.textAlign = "start";


        /*
          행성 글로우
        */''', "draw atmosphere")

# 7) 실시간 물리량: 경계까지 거리
sub(r'extraRow\s*=\s*row\(\s*"탈출 속도",\s*`\$\{escapeSpeed\.toFixed\(2\)\} m·s⁻¹`\s*\);',
    '''extraRow =
          row(
            "탈출 속도",
            `${escapeSpeed.toFixed(2)} m·s⁻¹`
          ) +
          row(
            "탈출 경계까지",
            `${Math.max(
              escapeBoundaryRadius() - Math.hypot(x, y),
              0
            ).toFixed(1)} m`
          );''', "extraRow")

# 8) 공식 설명 문구
sub(r'\n발사 방식\n',
    '\n탈출 경계: r = 2R (반투명 영역 바깥)\n경계를 넘을 때 E > 0 이면 탈출 성공\n\n발사 방식\n', "formula text")

# 9) 중복 id escapeAnswerBox 제거 (두 번째 것)
start = '<div id="escapeAnswerBox"'
first = s.find(start)
second = s.find(start, first + 1)
if first == -1 or second == -1:
    sys.exit("[실패] 중복 escapeAnswerBox를 찾지 못했습니다")
end = s.find("</div>", s.find("</p>", second)) + len("</div>")
s = s[:second] + s[end:]

out = "index_v1.4.3.html"
open(out, "w", encoding="utf-8").write(s)
print("완료:", out)
