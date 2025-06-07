document.addEventListener('DOMContentLoaded', () => {
  const viewStatsBtn = document.getElementById('view-stats-btn');
  const subjectSelect = document.getElementById('subject-select');
  const statsContainer = document.getElementById('subject-stats-container');
  const marksInfo = document.getElementById('marks-info');
  const attendanceInfo = document.getElementById('attendance-info');

  let scrapedData = null;

  viewStatsBtn.addEventListener('click', async () => {
    // Get form values
    const prn = document.getElementById('prn').value.trim();
    const day = document.querySelector('select[name="day"]').value.trim();
    const month = document.querySelector('select[name="month"]').value.trim();
    const year = document.querySelector('select[name="year"]').value.trim();

    if (!prn || !day || !month || !year) {
      alert("Please fill all the fields before viewing stats.");
      return;
    }

    // Prepare form data for POST
    const formData = new FormData();
    formData.append('prn', prn);
    formData.append('day', day);
    formData.append('month', month);
    formData.append('year', year);

    try {
      const response = await fetch('/fetch_stats', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errData = await response.json();
        alert("Error: " + (errData.error || "Failed to fetch data"));
        return;
      }

      const data = await response.json();
      scrapedData = data;

      // Get subjects from marks and attendance keys combined
      const subjects = new Set([
        ...Object.keys(data.marks || {}),
        ...Object.keys(data.attendance || {})
      ]);

      if (subjects.size === 0) {
        alert("No data available for these inputs.");
        return;
      }

      // Populate dropdown
      subjectSelect.innerHTML = '';
      subjects.forEach(sub => {
        const option = document.createElement('option');
        option.value = sub;
        option.textContent = sub;
        subjectSelect.appendChild(option);
      });

      statsContainer.style.display = 'block';
      updateStats(subjectSelect.value);

    } catch (error) {
      alert("Failed to fetch stats: " + error.message);
    }
  });

  subjectSelect.addEventListener('change', () => {
    updateStats(subjectSelect.value);
  });

  function updateStats(subject) {
    if (!scrapedData) return;

    // Marks
    const marks = scrapedData.marks && scrapedData.marks[subject];
    if (marks && marks.length) {
      marksInfo.textContent = marks.join(", ");
    } else {
      marksInfo.textContent = "No marks data";
    }

    // Attendance
    const attendance = scrapedData.attendance && scrapedData.attendance[subject];
    if (attendance !== undefined) {
      attendanceInfo.textContent = attendance;
    } else {
      attendanceInfo.textContent = "No attendance data";
    }
  }
});
