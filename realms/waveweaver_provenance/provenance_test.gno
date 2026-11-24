package waveweaver_provenance_v1

import (
	"strings"
	"testing"

	"chain/runtime"
	"gno.land/p/nt/uassert/v0"
)

func TestAnchorAndVerifyProvenance(t *testing.T) {
	alice := address("g1jg8mtutu9khhfwc4nxmuhcpftf0pajdhfvsqf5")
	testing.SetRealm(testing.NewUserRealm(alice))

	digest := "a3f901bc48e2901178c4de0923415689ab12cd34ef560123456789abcdef0123"
	receipt := AnchorPublication(
		cross,
		"WW-TEST-001",
		"ch-ai-quant",
		"576-Token Wick-Stripped Washout Study",
		"0x"+digest,
		942,
		4,
		3,
		"9:16_AVATAR_VIDEO,VISUAL_CAROUSEL,LONG_ARTICLE,PODCAST_AUDIO,MICRO_THREAD",
		"Empirical 576-token K-line backtest: 4.11% MaxDD vs 90.12% T+1h FOMO baseline.",
	)

	uassert.True(t, strings.HasPrefix(receipt, "ANCHORED:WW-TEST-001:"))
	uassert.Equal(t, 1, TotalPublications())
	uassert.Equal(t, 1, ChannelCount())

	verifyJSON := VerifyDigest(digest)
	uassert.True(t, strings.Contains(verifyJSON, `"verified":true`))
	uassert.True(t, strings.Contains(verifyJSON, `"qa_score":"94.2"`))

	homeMD := Render("")
	uassert.True(t, strings.Contains(homeMD, "WW-TEST-001"))
	detailMD := Render("pub/WW-TEST-001")
	uassert.True(t, strings.Contains(detailMD, "94.2 / 100.0"))
	_ = runtime.ChainID
}

func TestFailClosedOnLowQASlop(t *testing.T) {
	bob := address("g1jg8mtutu9khhfwc4nxmuhcpftf0pajdhfvsqf5")
	testing.SetRealm(testing.NewUserRealm(bob))

	uassert.AbortsWithMessage(
		t,
		"waveweaver: Stage 6 Anti-AI-Slop QA score below 850 permille (85.0%) minimum gate",
		func() {
			AnchorPublication(
				cross,
				"WW-SLOP-REJECT",
				"ch-ai-quant",
				"Unverified AI Slop Draft",
				"b4f901bc48e2901178c4de0923415689ab12cd34ef560123456789abcdef0124",
				720,
				0,
				2,
				"",
				"Should revert.",
			)
		},
	)
}
