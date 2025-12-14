document.addEventListener('DOMContentLoaded', () => {
    const matchesList = document.getElementById('matches-list');
    const matchesSection = document.getElementById('matches-section');
    const predictionSection = document.getElementById('prediction-section');
    const backBtn = document.getElementById('back-btn');

    // Team Background Mapping
    const teamBackgrounds = {
        'Manchester United FC': 'bruno_fernandes.png',
    };
    const defaultBackground = 'old_trafford.png';

    // Prediction Elements
    const pHomeName = document.getElementById('p-home-name');
    const pAwayName = document.getElementById('p-away-name');

    // New: Emblem elements for prediction view
    // We will inject these dynamically or assume the HTML structure needs them.
    // Let's modify the showPrediction logic to inject images directly into the DOM headers if simpler,
    // or we can select them if they existed. 
    // Since index.html doesn't have img tags yet, we will manipulate the DOM in showPrediction to add them or replace text content with HTML.

    const probHome = document.getElementById('prob-home');
    const probDraw = document.getElementById('prob-draw');
    const probAway = document.getElementById('prob-away');
    const labelHome = document.getElementById('label-home');
    const labelDraw = document.getElementById('label-draw');
    const labelAway = document.getElementById('label-away');
    const analysisText = document.getElementById('analysis-text');

    // Fetch Matches
    fetchMatches();

    backBtn.addEventListener('click', () => {
        predictionSection.classList.add('hidden');
        matchesSection.classList.remove('hidden');
        document.body.style.backgroundImage = url('');
    });

    async function fetchMatches() {
        try {
            const response = await fetch('/api/matches');
            const matches = await response.json();
            renderMatches(matches);
        } catch (error) {
            matchesList.innerHTML = '<div class="loading">試合データの取得に失敗しました。サーバーが起動しているか確認してください。</div>';
            console.error('Error:', error);
        }
    }

    function renderMatches(matches) {
        matchesList.innerHTML = '';
        if (matches.length === 0) {
            matchesList.innerHTML = '<div class="loading">予定されている試合はありません。</div>';
            return;
        }

        matches.forEach(match => {
            const date = new Date(match.utcDate).toLocaleDateString(undefined, {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            });

            // Use crest if available, otherwise fallback or empty
            const homeCrest = match.homeTeam.crest || '';
            const awayCrest = match.awayTeam.crest || '';

            const card = document.createElement('div');
            card.className = 'match-card';
            card.innerHTML = `
                <div class="match-date">${date}</div>
                <div class="match-info">
                    <div class="team-container">
                        ${homeCrest ? `<img src="${homeCrest}" class="team-crest-small" alt="${match.homeTeam.name}">` : ''}
                        <span class="team-name">${match.homeTeam.name}</span>
                    </div>
                    <span class="vs">VS</span>
                    <div class="team-container">
                        <span class="team-name">${match.awayTeam.name}</span>
                        ${awayCrest ? `<img src="${awayCrest}" class="team-crest-small" alt="${match.awayTeam.name}">` : ''}
                    </div>
                </div>
            `;

            card.addEventListener('click', () => showPrediction(match));
            matchesList.appendChild(card);
        });
    }

    async function showPrediction(match) {
        // UI Updates
        matchesSection.classList.add('hidden');
        predictionSection.classList.remove('hidden');

        // Dynamic Background Update
        let bgImage = defaultBackground;
        if (teamBackgrounds[match.homeTeam.name]) {
            bgImage = teamBackgrounds[match.homeTeam.name];
        } else if (teamBackgrounds[match.awayTeam.name]) {
            bgImage = teamBackgrounds[match.awayTeam.name];
        }
        document.body.style.backgroundImage = `url('$`{bgImage}')`;

        // Update Header with Emblems
        const matchHeader = document.querySelector('.match-header');
        const homeCrest = match.homeTeam.crest || '';
        const awayCrest = match.awayTeam.crest || '';

        // Safely constructing HTML for the header
        matchHeader.innerHTML = `
            <div class="team-display-large">
                ${homeCrest ? `<img src="${homeCrest}" class="team-crest-large" alt="${match.homeTeam.name}">` : ''}
                <div id="p-home-name" class="team-name-large">${match.homeTeam.name}</div>
            </div>
            <div class="vs-large">VS</div>
            <div class="team-display-large">
                ${awayCrest ? `<img src="${awayCrest}" class="team-crest-large" alt="${match.awayTeam.name}">` : ''}
                <div id="p-away-name" class="team-name-large">${match.awayTeam.name}</div>
            </div>
        `;

        // Reset state
        analysisText.innerHTML = 'AIが分析中... <span style="display:inline-block; animation: pulse 1s infinite">🤖</span>';
        setProbabilities(0, 0, 0);

        try {
            const encodedHome = encodeURIComponent(match.homeTeam.name);
            const encodedAway = encodeURIComponent(match.awayTeam.name);
            const url = `/api/predict?home_team=${encodedHome}&away_team=${encodedAway}&match_id=${match.id}`;

            const response = await fetch(url);
            const data = await response.json();

            const pred = data.prediction;
            setProbabilities(pred.home_win, pred.draw, pred.away_win);
            analysisText.textContent = pred.analysis;

        } catch (error) {
            analysisText.textContent = "予測の生成に失敗しました。もう一度お試しください。";
            console.error(error);
        }
    }

    function setProbabilities(home, draw, away) {
        const total = home + draw + away;
        if (total === 0) {
            probHome.style.width = '33%';
            probDraw.style.width = '34%';
            probAway.style.width = '33%';
            labelHome.textContent = '-';
            labelDraw.textContent = '-';
            labelAway.textContent = '-';
            return;
        }

        probHome.style.width = `${home}%`;
        probDraw.style.width = `${draw}%`;
        probAway.style.width = `${away}%`;

        labelHome.textContent = `${home}%`;
        labelDraw.textContent = `${draw}%`;
        labelAway.textContent = `${away}%`;
    }
});
