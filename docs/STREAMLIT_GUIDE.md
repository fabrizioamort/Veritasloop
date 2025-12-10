# VeritasLoop Streamlit Web Interface Guide

## Quick Start

### Launch the Application

```bash
# Using streamlit directly
streamlit run app.py

# Using uv (recommended)
uv run streamlit run app.py
```

The web interface will automatically open in your browser at http://localhost:8501

## User Interface Overview

### Main Components

1. **Sidebar** - Configuration and Help
   - Enable/Disable Phoenix Tracing
   - How it Works guide
   - Verdict types reference

2. **Input Section** - Submit Claims for Verification
   - Choice between Text or URL input
   - Text area for direct claim entry
   - URL input for news articles
   - Verification button

3. **Debate Arena** - Real-time Verification Process
   - Three-column layout showing agent interactions
   - Progress tracking and status updates

4. **Verdict Section** - Final Results
   - Color-coded verdict display
   - Detailed analysis and sources
   - Performance metrics

## How to Use

### Step 1: Choose Input Type

Select either **Testo** (Text) or **URL** using the radio buttons.

**Text Input Example:**
```
L'ISTAT ha dichiarato che l'inflazione è al 5%
```

**URL Input Example:**
```
https://www.ansa.it/sito/notizie/economia/2024/...
```

### Step 2: Enter Your Claim

- For **Text**: Enter the news claim or statement you want to verify
- For **URL**: Paste the full URL of the news article

### Step 3: Start Verification

Click the **🔍 Verifica** button to start the verification process.

### Step 4: Watch the Debate

The verification process unfolds in three columns:

#### Left Column: 🛡️ PRO Agent
- Displays arguments supporting the claim
- Shows sources corroborating the news
- Displays confidence level

#### Center Column: ⚖️ Arena
- Shows current processing stage
- Progress bar indicating rounds (1/3, 2/3, 3/3)
- Real-time status updates

#### Right Column: 🔍 CONTRA Agent
- Displays counter-arguments
- Shows contradictory evidence
- Identifies missing context or fallacies

### Step 5: Review the Verdict

After the debate concludes, the Judge's verdict appears with:

- **Verdict Type** with color coding:
  - ✅ **VERO** (True) - Green background
  - ❌ **FALSO** (False) - Red background
  - ⚠️ **PARZIALMENTE_VERO** (Partially True) - Yellow background
  - 🔍 **CONTESTO_MANCANTE** (Missing Context) - Purple background
  - ❓ **NON_VERIFICABILE** (Unverifiable) - Gray background

- **Confidence Score** (0-100%)
- **Summary** - Brief explanation in Italian
- **Analysis**:
  - PRO Agent strength assessment
  - CONTRA Agent strength assessment
  - Agreed facts (consensus)
  - Disputed points
- **Sources Used** - All sources with reliability indicators
- **Statistics**:
  - Processing time
  - Rounds completed
  - Total sources checked

### Step 6: Export Results (Optional)

Click **📄 Visualizza Output JSON** to view and copy the complete structured output.

## Advanced Features

### Phoenix Tracing

Enable visual observability of the verification process with automatic Phoenix server management:

1. Check **Abilita Tracing (Phoenix)** in the sidebar
2. The sidebar will show Phoenix status:
   - 🔭 **Phoenix: Online** - Already running
   - 🔭 **Phoenix: Will start with verification** - Will auto-start
   - 🔭 **Phoenix: Offline** - Not running
3. Click **Verifica** to start verification
   - Phoenix server automatically starts if not running
   - Traces are saved to `data/phoenix/traces.db`
4. Open http://localhost:6006 in a new browser tab
5. View detailed traces of:
   - Agent reasoning processes
   - Tool calls and searches
   - LLM prompts and responses
   - Performance metrics
6. Phoenix server persists after verification completes

**Key Features:**
- ✅ **Automatic startup** - No manual Phoenix server management needed
- ✅ **Persistent traces** - All traces saved to database
- ✅ **Status indicator** - See Phoenix status in sidebar
- ✅ **Reuse existing** - Connects to running Phoenix if available

### Understanding Source Reliability

Sources are marked with colored indicators:

- 🟢 **High Reliability** - Official sources, major news agencies, government sites
- 🟡 **Medium Reliability** - Established blogs, secondary sources
- 🔴 **Low Reliability** - Social media, unverified sources

### Interpreting Confidence Scores

Each agent displays a confidence score (0-100%):

- **80-100%**: Very confident in the position
- **60-79%**: Moderately confident
- **40-59%**: Uncertain, limited evidence
- **0-39%**: Low confidence, conflicting evidence

The final verdict confidence score represents the Judge's certainty in the decision.

## Example Workflows

### Example 1: Verifying a Political Claim

**Input (Text):**
```
Il governo ha aumentato le tasse del 10% nel 2024
```

**Process:**
1. PRO Agent searches for government sources, official decrees
2. CONTRA Agent looks for contradictory tax data, context
3. Debate unfolds over 3 rounds
4. Judge evaluates and delivers verdict

**Expected Result:**
- Verdict: PARZIALMENTE_VERO or CONTESTO_MANCANTE
- Explanation of which taxes increased and by how much
- Clarification of what was omitted from the claim

### Example 2: Verifying a Health News Article

**Input (URL):**
```
https://www.example.com/health/new-study-vaccine-effectiveness
```

**Process:**
1. System extracts article content
2. PRO Agent searches medical journals, health authorities
3. CONTRA Agent checks for study limitations, contradictory research
4. Scientific consensus is evaluated

**Expected Result:**
- Verdict: VERO, PARZIALMENTE_VERO, or NON_VERIFICABILE
- Links to original studies
- Context about study methodology and limitations

### Example 3: Verifying Viral Social Media Claim

**Input (Text):**
```
Video virale mostra politico che dice qualcosa di scioccante
```

**Process:**
1. PRO Agent searches for original video source
2. CONTRA Agent checks for deepfakes, context, full video
3. Debate focuses on authenticity and context

**Expected Result:**
- Verdict: FALSO, CONTESTO_MANCANTE, or NON_VERIFICABILE
- Original source if found
- Context explaining what was cut or manipulated

## Troubleshooting

### App Doesn't Start

**Error:** `ModuleNotFoundError: No module named 'streamlit'`
**Solution:**
```bash
uv pip install streamlit>=1.28.0
```

### Verification Fails

**Error:** API errors or timeouts
**Solutions:**
1. Check `.env` file has valid API keys
2. Verify internet connection
3. Check API rate limits (Brave Search, NewsAPI)

### Slow Performance

**Causes:**
- Complex claims requiring extensive research
- API rate limiting
- Many sources to fetch

**Solutions:**
- Wait for completion (typically <3 minutes)
- Use simpler, more specific claims
- Check network connection

### Phoenix Tracing Not Working

**Error:** Error message about Phoenix not being available
**Solution:**
```bash
uv pip install arize-phoenix openinference-instrumentation-langchain
```

**Error:** Phoenix server won't start
**Solutions:**
1. Check if port 6006 is already in use
2. Verify write permissions for `data/phoenix/` directory
3. Check the Streamlit logs for error details
4. Try starting Phoenix manually: `uv run phoenix serve`

## Tips for Best Results

1. **Be Specific**: Use clear, verifiable claims
   - ✅ Good: "L'ISTAT ha riportato inflazione al 5% a novembre 2024"
   - ❌ Bad: "L'economia va male"

2. **Use Recent News**: Better source availability
   - Claims from the last 6 months work best

3. **One Claim at a Time**: Don't mix multiple claims
   - ✅ Good: "Il governo ha approvato la riforma fiscale"
   - ❌ Bad: "Il governo ha approvato la riforma fiscale e aumentato la spesa sanitaria"

4. **Check Source Quality**: Review the sources used
   - Higher reliability sources = more trustworthy verdict

5. **Read the Full Analysis**: Don't just look at the verdict
   - Check consensus facts and disputed points
   - Understand the context

## Keyboard Shortcuts

Streamlit provides these default shortcuts:

- **R**: Rerun the app
- **C**: Clear cache
- **Q**: Show keyboard shortcuts
- **S**: Focus on search bar (if enabled)

## Privacy & Security

- All processing happens locally or through your API keys
- No data is stored permanently (session-based only)
- Phoenix traces are stored locally in `data/phoenix/traces.db`
- Sources are fetched in real-time (not stored)

## Performance Expectations

Typical verification times:

- **Simple text claim**: 60-90 seconds
- **URL extraction + verification**: 90-150 seconds
- **Complex multi-source verification**: 150-180 seconds

Maximum time limit: ~3 minutes per verification

## Further Customization

To customize the UI, edit `app.py`:

- **Colors**: Modify CSS in the `st.markdown()` section
- **Layout**: Adjust column ratios in `st.columns([1, 1, 1])`
- **Sidebar**: Add/remove configuration options
- **Verdict categories**: Match the categories in your `schemas.py`

## Support

For issues or questions:

1. Check the main README.md
2. Review PLANNING.md for system architecture
3. Check TASK.md for implementation details
4. Submit issues to the project repository

## Next Steps

After becoming familiar with the web interface, you can:

1. Use the CLI for automation and scripting
2. Enable Phoenix tracing for deep debugging
3. Contribute to Task 6.3 (Export & Sharing Features)
4. Build custom integrations using the Python API

---

**Enjoy using VeritasLoop!** 🔍
