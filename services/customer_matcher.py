import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

def clean_company_name(name):
    """Normalize company name by removing common suffixes and making lowercase."""
    if not name:
        return ""
    name = str(name).lower().strip()
    
    # Remove common suffixes that cause false negatives
    suffixes = [
        ' limited', ' ltd', ' ltd.',
        ' private limited', ' pvt ltd', ' pvt. ltd.', ' pvt. ltd', ' pvt.',
        ' corp', ' corp.', ' corporation',
        ' inc', ' inc.', ' incorporated',
        ' llc', ' l.l.c.',
        ' co.', ' co', ' company',
        ' industries', ' ind.',
        ' operations',
        ' l l c', ' fzco'
    ]
    
    # We loop multiple times to handle things like "Company Pvt Ltd"
    changed = True
    while changed:
        changed = False
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
                changed = True
                
    # Additional cleanups: remove punctuation like commas, dots
    name = name.replace('.', '').replace(',', '').replace('-', ' ')
    
    # Replace multiple spaces with single space
    import re
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name

def similarity_score(name1, name2):
    """Calculate similarity score between two cleaned names (0.0 to 1.0)."""
    return SequenceMatcher(None, name1, name2).ratio()

def find_best_match(target_name, customer_list, threshold=0.85):
    """
    Find the best matching customer from a list of defined customers.
    Returns (best_match_id, score) or (None, 0).
    customer_list should be [{'id': 1, 'primary_name': 'TechCorp', ...}, ...]
    """
    cleaned_target = clean_company_name(target_name)
    best_match = None
    best_score = 0.0
    
    # If the cleaned text falls under a threshold length, we might ignore fuzzy match
    # to avoid random short acronym matching.
    if len(cleaned_target) < 3:
        return None, 0.0
        
    for customer in customer_list:
        cleaned_cust = clean_company_name(customer['primary_name'])
        
        # Exact match after cleaning gets 1.0 immediately
        if cleaned_target == cleaned_cust:
            return customer['id'], 1.0
            
        score = similarity_score(cleaned_target, cleaned_cust)
        if score > best_score:
            best_score = score
            best_match = customer['id']
            
    if best_score >= threshold:
        return best_match, best_score
        
    return None, best_score
