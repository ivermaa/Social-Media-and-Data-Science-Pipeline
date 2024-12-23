document.addEventListener("DOMContentLoaded", function () {
    const menuButton = document.getElementById("menu-btn");
    const sidebar = document.querySelector(".sidebar");
    const content = document.querySelector(".content");

    // Toggle sidebar visibility
    menuButton.addEventListener("click", () => {
        sidebar.classList.toggle("expanded");
        content.classList.toggle("expanded");
    });

    const socket = io(); // Connect to the server using Socket.IO

    // Real-time toxic comments visualization
    const chartDiv = document.getElementById("real-time-chart");
    const yearSelect = document.getElementById("year");
    const monthSelect = document.getElementById("month");

    function updateRealTimeChart(year, month) {
        const params = new URLSearchParams();
        if (year) params.append("year", year);
        if (month) params.append("month", month);

        fetch(`/real-time-data?${params.toString()}`)
            .then((response) => response.json())
            .then((data) => {
                const dates = data.map((d) => d.date);
                const counts = data.map((d) => d.count);

                const trace = {
                    x: dates,
                    y: counts,
                    type: 'bar',
                    text: counts,
                    hovertemplate: '<b>Date:</b> %{x}<br><b>Count:</b> %{text}<extra></extra>',
                    marker: { color: 'blue' },
                };

                const layout = {
                    title: 'Real-Time Toxic Comment Counts',
                    xaxis: { title: 'Date' },
                    yaxis: { title: 'Toxic Comments' },
                };

                Plotly.newPlot(chartDiv, [trace], layout);
            })
            .catch((error) => console.error('Error fetching real-time data:', error));
    }

    // Initialize real-time chart with default filters
    updateRealTimeChart(yearSelect.value, monthSelect.value);

    // Update real-time chart when filters change
    yearSelect.addEventListener("change", () => {
        updateRealTimeChart(yearSelect.value, monthSelect.value);
    });

    monthSelect.addEventListener("change", () => {
        updateRealTimeChart(yearSelect.value, monthSelect.value);
    });

    // Listen for real-time updates from the server via Socket.IO
    socket.on('real-time-update', (message) => {
        console.log('Real-time update received:', message);
        const year = yearSelect.value;
        const month = monthSelect.value;

        // Filter real-time updates based on selected year and month
        if (
            (!year || message.year === year) &&
            (!month || message.month === month)
        ) {
            updateRealTimeChart(year, month);
        }
    });

    // Cumulative posts visualization
    const subredditSelect = document.getElementById("subreddit-select");
    const cumulativeChartDiv = document.getElementById("cumulative-chart");
    const toxicityRadios = document.getElementsByName("toxicity"); // Get the radio buttons

    // Function to get the selected toxicity value
    function getSelectedToxicity() {
        for (const radio of toxicityRadios) {
            if (radio.checked) {
                return radio.value;
            }
        }
        return ""; // Default to all if no selection
    }

    async function updateCumulativeChart() {
        const subreddit = subredditSelect.value;
        const toxicity = getSelectedToxicity();

        const params = new URLSearchParams();
        params.append("subreddit", subreddit);
        params.append("toxicity", toxicity);

        if (subreddit === "all") {
            const allSubreddits = ["Politics", "cloudcomputing", "Programming", "datascience", "Technology", "pol (4chan)"];
            const colors = ["blue", "red", "green", "purple", "orange", "brown"];
            const traces = [];

            for (let i = 0; i < allSubreddits.length; i++) {
                params.set("subreddit", allSubreddits[i]);

                const response = await fetch(`/cumulative-data?${params.toString()}`);
                const data = await response.json();

                const dates = data.map((d) => d.ingestion_date);
                const counts = data.map((d) => d.cumulative_posts);

                traces.push({
                    x: dates,
                    y: counts,
                    type: 'scatter',
                    mode: 'lines+markers',
                    name: allSubreddits[i],
                    marker: { color: colors[i] },
                });
            }

            const layout = {
                title: `Cumulative Posts Over Time (All Subreddits and Boards) [Toxicity: ${toxicity || "All"}]`,
                xaxis: { title: 'Ingestion Date' },
                yaxis: { title: 'Cumulative Posts' },
            };

            Plotly.newPlot(cumulativeChartDiv, traces, layout);
        } else {
            const response = await fetch(`/cumulative-data?${params.toString()}`);
            const data = await response.json();

            const dates = data.map((d) => d.ingestion_date);
            const counts = data.map((d) => d.cumulative_posts);

            const trace = {
                x: dates,
                y: counts,
                type: 'scatter',
                mode: 'lines+markers',
                name: subreddit,
            };

            const layout = {
                title: `Cumulative Posts Over Time for ${subreddit} [Toxicity: ${toxicity || "All"}]`,
                xaxis: { title: 'Ingestion Date' },
                yaxis: { title: 'Cumulative Posts' },
            };

            Plotly.newPlot(cumulativeChartDiv, [trace], layout);
        }
    }

    // Update cumulative chart on subreddit or toxicity filter change
    subredditSelect.addEventListener("change", updateCumulativeChart);
    toxicityRadios.forEach((radio) => radio.addEventListener("change", updateCumulativeChart));

    // Initialize cumulative chart on page load
    updateCumulativeChart();

    // -----
    const platformSelect = document.getElementById("platform-select");
    const metricSelect = document.getElementById("metric-select");
    const engagementChartDiv = document.getElementById("popularity-engagement-chart");

    function updatePopularityEngagementChart(platform, metric) {
        const params = new URLSearchParams();
        params.append("platform", platform);
        params.append("metric", metric);

        fetch(`/popularity-engagement-data?${params.toString()}`)
            .then((response) => response.json())
            .then((data) => {
                if (data.error) {
                    console.error("Error fetching data:", data.error);
                    return;
                }

                const platforms = data.map((d) => d.platform);
                const metricValues = data.map((d) => d.metric_value);

                const trace = {
                    x: platforms,
                    y: metricValues,
                    type: 'bar',
                    text: metricValues,
                    hovertemplate: '<b>Subreddit:</b> %{x}<br><b>Value:</b> %{text}<extra></extra>',
                    marker: { color: metric === 'subscribers' ? 'green' : 'orange' },
                };

                const layout = {
                    title: `Popularity and Engagement Analysis: Subreddit (${metric})`,
                    xaxis: { title: 'Subreddit', tickangle: -45 },
                    yaxis: { title: metric === 'subscribers' ? 'Subscribers Count' : 'Comments Count' },
                };

                Plotly.newPlot(engagementChartDiv, [trace], layout);
            })
            .catch((error) => console.error('Error fetching popularity and engagement data:', error));
    }

    // Event listeners for platform and metric selection
    platformSelect.addEventListener("change", () => {
        updatePopularityEngagementChart(platformSelect.value, metricSelect.value);
    });

    metricSelect.addEventListener("change", () => {
        updatePopularityEngagementChart(platformSelect.value, metricSelect.value);
    });

    // Initialize chart with default values
    updatePopularityEngagementChart(platformSelect.value, metricSelect.value);

});
