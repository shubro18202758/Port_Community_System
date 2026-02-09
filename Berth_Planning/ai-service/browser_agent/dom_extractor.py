"""
DOM Extractor for Browser Agent
Extracts and normalizes DOM content for LLM consumption
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


@dataclass
class DOMElement:
    """Represents an interactive DOM element"""
    tag: str
    element_id: Optional[str]
    classes: List[str]
    text: str
    role: Optional[str]
    aria_label: Optional[str]
    data_testid: Optional[str]
    href: Optional[str]
    selector: str  # CSS selector to target this element
    is_interactive: bool
    bounding_box: Optional[Dict[str, int]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tag": self.tag,
            "id": self.element_id,
            "classes": self.classes,
            "text": self.text[:100] if self.text else "",  # Truncate long text
            "role": self.role,
            "aria_label": self.aria_label,
            "data_testid": self.data_testid,
            "selector": self.selector,
            "is_interactive": self.is_interactive
        }


class DOMExtractor:
    """
    Extracts and processes DOM content for the browser agent.
    Focuses on interactive elements and meaningful content.
    """
    
    # Interactive element tags
    INTERACTIVE_TAGS = {
        'a', 'button', 'input', 'select', 'textarea', 
        'details', 'summary', 'label'
    }
    
    # Interactive roles
    INTERACTIVE_ROLES = {
        'button', 'link', 'checkbox', 'radio', 'textbox',
        'combobox', 'listbox', 'menuitem', 'tab', 'switch',
        'slider', 'spinbutton', 'searchbox'
    }
    
    # Elements to skip
    SKIP_TAGS = {'script', 'style', 'noscript', 'svg', 'path', 'meta', 'link'}
    
    def __init__(self, max_elements: int = 100, max_text_length: int = 5000):
        """
        Initialize DOM extractor.
        
        Args:
            max_elements: Maximum interactive elements to extract
            max_text_length: Maximum text content length
        """
        self.max_elements = max_elements
        self.max_text_length = max_text_length
    
    def extract_from_html(self, html: str, url: str = "") -> Dict[str, Any]:
        """
        Extract structured data from HTML content.
        
        Args:
            html: Raw HTML content
            url: Current page URL
            
        Returns:
            Structured DOM data for LLM
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract page metadata
        title = soup.title.string if soup.title else ""
        
        # Extract interactive elements
        interactive_elements = self._extract_interactive_elements(soup)
        
        # Extract text content (for summarization)
        text_content = self._extract_text_content(soup)
        
        # Extract data tables
        tables = self._extract_tables(soup)
        
        # Build page structure
        structure = self._build_page_structure(soup)
        
        return {
            "url": url,
            "title": title,
            "interactive_elements": [e.to_dict() for e in interactive_elements[:self.max_elements]],
            "text_content": text_content[:self.max_text_length],
            "tables": tables[:5],  # Max 5 tables
            "structure": structure,
            "element_count": len(interactive_elements)
        }
    
    def _extract_interactive_elements(self, soup: BeautifulSoup) -> List[DOMElement]:
        """Extract all interactive elements from the page"""
        elements = []
        element_index = 0
        
        for tag in soup.find_all(True):
            if tag.name in self.SKIP_TAGS:
                continue
            
            is_interactive = self._is_interactive(tag)
            if not is_interactive:
                continue
            
            element = self._create_dom_element(tag, element_index)
            if element:
                elements.append(element)
                element_index += 1
                
            if len(elements) >= self.max_elements:
                break
        
        return elements
    
    def _is_interactive(self, tag) -> bool:
        """Check if an element is interactive"""
        # Check tag name
        if tag.name in self.INTERACTIVE_TAGS:
            return True
        
        # Check role attribute
        role = tag.get('role', '')
        if role in self.INTERACTIVE_ROLES:
            return True
        
        # Check for click handlers
        if tag.get('onclick') or tag.get('ng-click') or tag.get('@click'):
            return True
        
        # Check for tabindex (makes element focusable)
        tabindex = tag.get('tabindex')
        if tabindex and tabindex != '-1':
            return True
        
        # Check for data-testid (testing attribute often on interactive elements)
        if tag.get('data-testid'):
            return True
        
        # Check for cursor-pointer class (common in React apps)
        classes = tag.get('class', [])
        if isinstance(classes, list):
            classes_str = ' '.join(classes)
        else:
            classes_str = classes
        
        if 'cursor-pointer' in classes_str or 'clickable' in classes_str:
            return True
        
        return False
    
    def _create_dom_element(self, tag, index: int) -> Optional[DOMElement]:
        """Create a DOMElement from a BeautifulSoup tag"""
        try:
            # Get element text
            text = tag.get_text(strip=True)[:200]  # Truncate long text
            
            # Build CSS selector
            selector = self._build_selector(tag, index)
            
            # Get classes
            classes = tag.get('class', [])
            if isinstance(classes, str):
                classes = classes.split()
            
            return DOMElement(
                tag=tag.name,
                element_id=tag.get('id'),
                classes=classes[:5],  # Max 5 classes
                text=text,
                role=tag.get('role'),
                aria_label=tag.get('aria-label'),
                data_testid=tag.get('data-testid'),
                href=tag.get('href'),
                selector=selector,
                is_interactive=True
            )
        except Exception as e:
            logger.warning(f"Error creating DOM element: {e}")
            return None
    
    def _build_selector(self, tag, index: int) -> str:
        """Build a CSS selector for the element"""
        # Prefer data-testid
        if tag.get('data-testid'):
            return f'[data-testid="{tag.get("data-testid")}"]'
        
        # Then prefer ID
        if tag.get('id'):
            return f'#{tag.get("id")}'
        
        # Then prefer aria-label
        if tag.get('aria-label'):
            return f'[aria-label="{tag.get("aria-label")}"]'
        
        # Build composite selector
        parts = [tag.name]
        
        classes = tag.get('class', [])
        if classes:
            if isinstance(classes, str):
                classes = classes.split()
            # Use first meaningful class
            for cls in classes[:2]:
                if not cls.startswith('_') and len(cls) < 30:
                    parts.append(f'.{cls}')
                    break
        
        # Add text content hint for buttons/links
        text = tag.get_text(strip=True)[:30]
        if text and tag.name in ['button', 'a']:
            return f'{tag.name}:has-text("{text}")'
        
        return ''.join(parts)
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract meaningful text content from the page"""
        # Remove script and style elements
        for tag in soup.find_all(['script', 'style', 'noscript', 'svg']):
            tag.decompose()
        
        # Get text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def _extract_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract data tables from the page"""
        tables = []
        
        for table in soup.find_all('table'):
            table_data = {
                "headers": [],
                "rows": []
            }
            
            # Extract headers
            headers = table.find_all('th')
            table_data["headers"] = [h.get_text(strip=True) for h in headers[:10]]
            
            # Extract rows (max 10)
            for row in table.find_all('tr')[:10]:
                cells = row.find_all(['td', 'th'])
                row_data = [c.get_text(strip=True)[:50] for c in cells[:10]]
                if row_data and row_data != table_data["headers"]:
                    table_data["rows"].append(row_data)
            
            if table_data["rows"]:
                tables.append(table_data)
        
        return tables
    
    def _build_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Build a hierarchical structure of the page"""
        structure = {
            "header": bool(soup.find(['header', '[role="banner"]'])),
            "nav": bool(soup.find(['nav', '[role="navigation"]'])),
            "main": bool(soup.find(['main', '[role="main"]'])),
            "sidebar": bool(soup.find(['aside', '[role="complementary"]'])),
            "footer": bool(soup.find(['footer', '[role="contentinfo"]'])),
            "forms": len(soup.find_all('form')),
            "buttons": len(soup.find_all('button')),
            "links": len(soup.find_all('a')),
            "inputs": len(soup.find_all('input'))
        }
        return structure
    
    def create_llm_context(self, dom_data: Dict[str, Any], task: str) -> str:
        """
        Create a compact text representation for the LLM.
        
        Args:
            dom_data: Extracted DOM data
            task: Current task description
            
        Returns:
            Formatted text for LLM context
        """
        lines = [
            f"## Current Page: {dom_data.get('title', 'Unknown')}",
            f"URL: {dom_data.get('url', 'Unknown')}",
            "",
            "## Page Structure:",
            f"- Interactive elements: {dom_data.get('element_count', 0)}",
            f"- Tables: {len(dom_data.get('tables', []))}",
            ""
        ]
        
        # Add interactive elements
        elements = dom_data.get('interactive_elements', [])
        if elements:
            lines.append("## Interactive Elements:")
            for i, elem in enumerate(elements[:30], 1):  # Limit to 30 for context window
                elem_desc = f"{i}. [{elem['tag']}]"
                if elem.get('text'):
                    elem_desc += f' "{elem["text"][:40]}"'
                if elem.get('data_testid'):
                    elem_desc += f' (testid: {elem["data_testid"]})'
                elem_desc += f' -> {elem["selector"]}'
                lines.append(elem_desc)
            lines.append("")
        
        # Add text content summary
        text = dom_data.get('text_content', '')
        if text:
            lines.append("## Page Content Summary:")
            lines.append(text[:2000])  # First 2000 chars
            lines.append("")
        
        # Add table data
        tables = dom_data.get('tables', [])
        for i, table in enumerate(tables[:2], 1):  # Max 2 tables
            lines.append(f"## Table {i}:")
            if table.get('headers'):
                lines.append(f"Headers: {' | '.join(table['headers'][:5])}")
            for row in table.get('rows', [])[:5]:
                lines.append(f"  {' | '.join(str(c)[:20] for c in row[:5])}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def find_element_for_task(
        self, 
        dom_data: Dict[str, Any], 
        description: str
    ) -> Optional[str]:
        """
        Find the best element selector for a described element.
        
        Args:
            dom_data: Extracted DOM data
            description: Natural language description of the element
            
        Returns:
            CSS selector or None
        """
        description_lower = description.lower()
        elements = dom_data.get('interactive_elements', [])
        
        # Score each element
        scored_elements: List[Tuple[float, DOMElement]] = []
        
        for elem in elements:
            score = 0.0
            
            # Check text match
            if elem.get('text'):
                text_lower = elem['text'].lower()
                if description_lower in text_lower:
                    score += 0.5
                elif any(word in text_lower for word in description_lower.split()):
                    score += 0.3
            
            # Check aria-label match
            if elem.get('aria_label'):
                label_lower = elem['aria_label'].lower()
                if description_lower in label_lower:
                    score += 0.4
            
            # Check data-testid match
            if elem.get('data_testid'):
                testid_lower = elem['data_testid'].lower()
                if any(word in testid_lower for word in description_lower.split()):
                    score += 0.3
            
            # Check tag relevance
            if 'button' in description_lower and elem['tag'] == 'button':
                score += 0.1
            if 'link' in description_lower and elem['tag'] == 'a':
                score += 0.1
            if 'input' in description_lower and elem['tag'] == 'input':
                score += 0.1
            
            if score > 0:
                scored_elements.append((score, elem))
        
        # Return best match
        if scored_elements:
            scored_elements.sort(key=lambda x: x[0], reverse=True)
            return scored_elements[0][1]['selector']
        
        return None
