document.addEventListener("DOMContentLoaded", function () {
    // Sidebar functionality
    const menuButton = document.getElementById("menu-btn");
    const sidebar = document.querySelector(".sidebar");
    const content = document.querySelector(".content");

    menuButton.addEventListener("click", () => {
        sidebar.classList.toggle("expanded");
        content.classList.toggle("expanded");
    });

    // Real-time toxic comments visualization
    const filterBtn = document.getElementById("filter-btn");
    const yearSelect = document.getElementById("year");
    const monthSelect = document.getElementById("month");
    const chartDiv = document.getElementById("real-time-chart");

    filterBtn.addEventListener("click", async () => {
        const year = yearSelect.value;
        const month = monthSelect.value;

        const response = await fetch(`/real-time-data?year=${year}&month=${month}`);
        const data = await response.json();

        const dates = data.map((d) => d.date);
        const counts = data.map((d) => d.count);

        const trace = {
            x: dates,
            y: counts,
            type: 'bar',
            text: counts, // Display counts as hover text
            hovertemplate: '<b>Date:</b> %{x}<br><b>Count:</b> %{text}<extra></extra>', // Customize hover text
            marker: {
                color: 'blue',
            },
        };

        const layout = {
            title: 'Real-Time Toxic Comment Counts',
            xaxis: { title: 'Date' },
            yaxis: { title: 'Toxic Comments' },
        };

        Plotly.newPlot(chartDiv, [trace], layout);
    });

    // Cumulative posts visualization
    const cumulativeFilterBtn = document.getElementById("cumulative-filter-btn");
    const subredditSelect = document.getElementById("subreddit-select");
    const cumulativeChartDiv = document.getElementById("cumulative-chart");

    cumulativeFilterBtn.addEventListener("click", async () => {
        const subreddit = subredditSelect.value;

        if (subreddit === "all") {
            // Fetch data for all subreddits and boards
            const allSubreddits = ["t5_2cneq", "t5_2rbzr", "t5_2fwo", "t5_2sptq", "t5_2qh16", "pol"];
            const colors = ["blue", "red", "green", "purple", "orange", "brown"];
            const traces = [];

            for (let i = 0; i < allSubreddits.length; i++) {
                const response = await fetch(`/cumulative-data?subreddit=${allSubreddits[i]}`);
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
                title: 'Cumulative Posts Over Time (All Subreddits and Boards)',
                xaxis: { title: 'Ingestion Date' },
                yaxis: { title: 'Cumulative Posts' },
            };

            Plotly.newPlot(cumulativeChartDiv, traces, layout);
        } else {
            // Fetch data for a specific subreddit or board
            const response = await fetch(`/cumulative-data?subreddit=${subreddit}`);
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
                title: `Cumulative Posts Over Time for ${subreddit}`,
                xaxis: { title: 'Ingestion Date' },
                yaxis: { title: 'Cumulative Posts' },
            };

            Plotly.newPlot(cumulativeChartDiv, [trace], layout);
        }
    });
});
