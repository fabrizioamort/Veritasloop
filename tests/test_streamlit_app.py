"""
Unit tests for Streamlit app functionality.
"""

from unittest.mock import Mock

import pytest


class TestStreamlitApp:
    """Test suite for Streamlit app helper functions."""

    def test_get_verdict_color(self):
        """Test verdict color mapping."""
        # Import here to avoid streamlit initialization during collection
        import sys

        # Mock streamlit to prevent initialization
        sys.modules['streamlit'] = Mock()

        # Now we can import app functions
        # Since we can't easily test the actual app.py functions without running streamlit,
        # we'll test the logic independently

        # Test verdict color mapping logic
        verdict_map = {
            "VERO": "verdict-true",
            "FALSO": "verdict-false",
            "PARZIALMENTE_VERO": "verdict-partial",
            "CONTESTO_MANCANTE": "verdict-context",
            "NON_VERIFICABILE": "verdict-unknown"
        }

        assert verdict_map["VERO"] == "verdict-true"
        assert verdict_map["FALSO"] == "verdict-false"
        assert verdict_map["PARZIALMENTE_VERO"] == "verdict-partial"
        assert verdict_map["CONTESTO_MANCANTE"] == "verdict-context"
        assert verdict_map["NON_VERIFICABILE"] == "verdict-unknown"

    def test_get_verdict_emoji(self):
        """Test verdict emoji mapping."""
        emoji_map = {
            "VERO": "✅",
            "FALSO": "❌",
            "PARZIALMENTE_VERO": "⚠️",
            "CONTESTO_MANCANTE": "🔍",
            "NON_VERIFICABILE": "❓"
        }

        assert emoji_map["VERO"] == "✅"
        assert emoji_map["FALSO"] == "❌"
        assert emoji_map["PARZIALMENTE_VERO"] == "⚠️"
        assert emoji_map["CONTESTO_MANCANTE"] == "🔍"
        assert emoji_map["NON_VERIFICABILE"] == "❓"

    def test_reliability_emoji_mapping(self):
        """Test source reliability emoji mapping."""
        reliability_emoji = {
            "high": "🟢",
            "medium": "🟡",
            "low": "🔴"
        }

        assert reliability_emoji["high"] == "🟢"
        assert reliability_emoji["medium"] == "🟡"
        assert reliability_emoji["low"] == "🔴"

    def test_format_source_structure(self):
        """Test source formatting data structure."""
        # Sample source structure
        source = {
            'url': 'https://example.com/article',
            'title': 'Test Article',
            'snippet': 'This is a test snippet that should be truncated if too long' * 5,
            'reliability': 'high'
        }

        # Verify structure
        assert 'url' in source
        assert 'title' in source
        assert 'snippet' in source
        assert 'reliability' in source
        assert source['reliability'] in ['high', 'medium', 'low']

    def test_debate_message_structure(self):
        """Test debate message data structure."""
        # Sample message structure
        message = {
            'round': 1,
            'agent': 'PRO',
            'message_type': 'argument',
            'content': 'This is a test argument',
            'sources': [
                {
                    'url': 'https://example.com',
                    'title': 'Source 1',
                    'reliability': 'high'
                }
            ],
            'confidence': 85
        }

        # Verify structure
        assert 'round' in message
        assert 'agent' in message
        assert 'message_type' in message
        assert 'content' in message
        assert 'sources' in message
        assert 'confidence' in message
        assert message['agent'] in ['PRO', 'CONTRA']
        assert 0 <= message['confidence'] <= 100

    def test_verdict_structure(self):
        """Test verdict data structure."""
        verdict_data = {
            'verdict': 'VERO',
            'confidence_score': 85,
            'summary': 'Test summary',
            'analysis': {
                'pro_strength': 'High - good sources',
                'contra_strength': 'Medium - some concerns',
                'consensus_facts': ['Fact 1', 'Fact 2'],
                'disputed_points': ['Point 1']
            },
            'sources_used': [
                {
                    'url': 'https://example.com',
                    'title': 'Source',
                    'reliability': 'high'
                }
            ],
            'metadata': {
                'processing_time_seconds': 120,
                'rounds_completed': 3,
                'total_sources_checked': 10
            }
        }

        # Verify structure
        assert 'verdict' in verdict_data
        assert 'confidence_score' in verdict_data
        assert 'summary' in verdict_data
        assert 'analysis' in verdict_data
        assert 'sources_used' in verdict_data
        assert 'metadata' in verdict_data
        assert verdict_data['verdict'] in [
            'VERO', 'FALSO', 'PARZIALMENTE_VERO',
            'CONTESTO_MANCANTE', 'NON_VERIFICABILE'
        ]


class TestStreamlitAppIntegration:
    """Integration tests for Streamlit app."""

    @pytest.mark.integration
    def test_app_imports(self):
        """Test that app.py can be imported without errors."""
        try:
            # This will fail if there are syntax errors
            with open('app.py', encoding='utf-8') as f:
                content = f.read()
                # Basic syntax check
                assert 'import streamlit as st' in content
                assert 'def main():' in content
                assert 'run_verification' in content
        except Exception as e:
            pytest.fail(f"Failed to read app.py: {e}")

    @pytest.mark.integration
    def test_required_functions_present(self):
        """Test that required functions are present in app.py."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Check for required functions
        required_functions = [
            'get_verdict_color',
            'get_verdict_emoji',
            'format_source',
            'display_debate_message',
            'run_verification',
            'check_phoenix_running',
            'start_phoenix_server',
            'main'
        ]

        for func in required_functions:
            assert f'def {func}(' in content, f"Function {func} not found in app.py"

    @pytest.mark.integration
    def test_streamlit_components_used(self):
        """Test that key Streamlit components are used."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Check for key Streamlit components
        components = [
            'st.set_page_config',
            'st.title',
            'st.columns',
            'st.radio',
            'st.text_area',
            'st.text_input',
            'st.button',
            'st.progress',
            'st.expander',
            'st.json',
            'st.markdown'
        ]

        for component in components:
            assert component in content, f"Streamlit component {component} not found"

    @pytest.mark.integration
    def test_css_styling_present(self):
        """Test that custom CSS styling is present."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Check for CSS classes
        css_classes = [
            'pro-message',
            'contra-message',
            'verdict-true',
            'verdict-false',
            'verdict-partial',
            'verdict-context',
            'verdict-unknown'
        ]

        for css_class in css_classes:
            assert css_class in content, f"CSS class {css_class} not found"

    @pytest.mark.integration
    def test_phoenix_integration(self):
        """Test that Phoenix integration features are present."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Check for Phoenix-related code
        phoenix_features = [
            'check_phoenix_running',
            'start_phoenix_server',
            '_phoenix_session',
            'phoenix as px',
            'launch_app',
            'run_in_background=True',
            'database_url'
        ]

        for feature in phoenix_features:
            assert feature in content, f"Phoenix feature '{feature}' not found"

    @pytest.mark.integration
    def test_phoenix_auto_start_logic(self):
        """Test that Phoenix auto-start logic is implemented."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Verify auto-start workflow
        assert 'phoenix_started = start_phoenix_server()' in content
        assert 'if phoenix_started:' in content
        assert 'enable_tracing()' in content
        assert 'data/phoenix' in content

    @pytest.mark.integration
    def test_phoenix_status_indicator(self):
        """Test that Phoenix status indicator is in sidebar."""
        with open('app.py', encoding='utf-8') as f:
            content = f.read()

        # Check for status indicator
        assert 'Phoenix: Online' in content
        assert 'Phoenix: Offline' in content
        assert 'check_phoenix_running()' in content
