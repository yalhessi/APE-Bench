"""
APE Bench Train/Test Split Strategy

Design principles:
1. Multi-dimensional stratified sampling for test set, ensure all categories are evenly represented
2. Ensure minimum quota for rare categories in test set
3. Avoid excessive concentration of modifications in the same file
4. Prioritize selecting data updated in the same conditions
5. Selected data goes to test set, remaining data goes to train set
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict, Counter
from datetime import datetime


class StratifiedSplitter:
    """Stratified train/test splitter"""

    def __init__(self, data: List[Dict[str, Any]]):
        """
        Initialize splitter

        Args:
            data: Complete task data list
        """
        self.data = data
        
        # Parse time field
        for item in self.data:
            # commit_date may be in metadata, or at the top level
            date_str = None
            if 'metadata' in item and 'commit_date' in item['metadata']:
                date_str = item['metadata']['commit_date']
            elif 'commit_date' in item:
                date_str = item['commit_date']
            
            if date_str:
                item['_parsed_date'] = datetime.fromisoformat(date_str)
            else:
                item['_parsed_date'] = datetime.min
    
    def sample(self, n: int, strategy: str = 'balanced') -> List[Dict[str, Any]]:
        """
        Execute sampling
        
        Args:
            n: Sampling number
            strategy: Sampling strategy
                - 'balanced': Balanced strategy (default)
                - 'proportional': Proportional strategy
                - 'difficulty_focused': Difficulty focused strategy
        
        Returns:
            Sampled data list
        """
        if n >= len(self.data):
            return self.data.copy()
        
        if strategy == 'balanced':
            return self._balanced_sampling(n)
        elif strategy == 'proportional':
            return self._proportional_sampling(n)
        elif strategy == 'difficulty_focused':
            return self._difficulty_focused_sampling(n)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def split(self, test_size: int, strategy: str = 'balanced') -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Split data into train and test sets

        Args:
            test_size: Number of samples for test set
            strategy: Sampling strategy for test set

        Returns:
            Tuple of (test_data, train_data)
        """
        test_data = self.sample(test_size, strategy=strategy)
        test_ids = {id(item) for item in test_data}
        train_data = [item for item in self.data if id(item) not in test_ids]
        return test_data, train_data

    def _balanced_sampling(self, n: int) -> List[Dict[str, Any]]:
        """
        Balanced sampling strategy: ensure all dimensions are evenly covered
        
        Core ideas:
        1. Prioritize retaining all bug fix and chore tasks (rare categories)
        2. Difficulty distribution uses normal distribution (centered on medium)
        3. formalization_aspect uses balanced allocation, avoiding excessive concentration of new_mathematics
        4. Maximum selection of the same file
        5. Selection in the same layer in reverse chronological order
        """
        # Step 1: Group by category and difficulty
        category_groups = defaultdict(list)
        for item in self.data:
            category = item['metadata']['task_category']
            category_groups[category].append(item)
        
        # Sort by time
        for category in category_groups:
            category_groups[category].sort(
                key=lambda x: x['_parsed_date'],
                reverse=True
            )
        
        # Step 2: Retain all rare categories (bug fix and chore)
        selected = []
        remaining_quota = n
        
        for rare_category in ['bug fix', 'chore']:
            if rare_category in category_groups:
                items = category_groups[rare_category]
                selected.extend(items)
                remaining_quota -= len(items)
                del category_groups[rare_category]
        
        if remaining_quota <= 0:
            return selected[:n]
        
        # Step 3: Count the distribution of each dimension of the remaining data
        remaining_data = [item for item in self.data if item not in selected]
        
        aspect_difficulty_groups = defaultdict(list)
        for item in remaining_data:
            aspect = item['metadata']['formalization_aspect']
            difficulty = item['metadata']['difficulty']
            key = f"{aspect}_{difficulty}"
            aspect_difficulty_groups[key].append(item)
        
        # Sort each group by time (newest first)
        for key in aspect_difficulty_groups:
            aspect_difficulty_groups[key].sort(
                key=lambda x: x['_parsed_date'],
                reverse=True
            )
        
        # Step 4: Design the difficulty quota of the normal distribution
        # Target distribution (smooth normal distribution centered on medium, reducing kurtosis, balancing easy and hard):
        # very easy: ~3%, easy: ~6%, medium: ~40%, hard: ~48%, very hard: ~3%
        difficulty_quotas = {
            'very easy': max(1, int(remaining_quota * 0.03)),
            'easy': int(remaining_quota * 0.06),
            'medium': int(remaining_quota * 0.40),
            'hard': int(remaining_quota * 0.48),
            'very hard': max(1, int(remaining_quota * 0.03))
        }
        
        # Adjust the quota so that the total equals remaining_quota
        total_allocated = sum(difficulty_quotas.values())
        if total_allocated < remaining_quota:
            difficulty_quotas['medium'] += remaining_quota - total_allocated
        elif total_allocated > remaining_quota:
            difficulty_quotas['medium'] -= total_allocated - remaining_quota
        
        # Step 5: Design the balanced aspect quota (avoid excessive concentration of new_mathematics)
        # Target distribution: evenly distribute the aspects, considering the original data amount.
        aspects = ['new_mathematics', 'structural_design', 'mathematical_abstraction',
                  'proof_technique', 'technical_implementation']
        
        # Calculate the proportion of each aspect in the remaining data
        aspect_counts_in_data = defaultdict(int)
        for item in remaining_data:
            aspect_counts_in_data[item['metadata']['formalization_aspect']] += 1
        
        total_remaining_data = len(remaining_data)
        
        # Design the weighted quota: reduce the weight of the aspects that are excessively concentrated, increase the weight of the rare aspects.
        aspect_weights = {}
        for aspect in aspects:
            original_proportion = aspect_counts_in_data.get(aspect, 0) / total_remaining_data if total_remaining_data > 0 else 0
            # Reduce the weight of the aspects that are more than 30% of the total, increase the weight of the aspects that are less than 15% of the total.
            if original_proportion > 0.3:
                aspect_weights[aspect] = original_proportion * 0.7  # Reduce the weight by 30%
            elif original_proportion < 0.15:
                aspect_weights[aspect] = original_proportion * 1.3  # Increase the weight by 30%
            else:
                aspect_weights[aspect] = original_proportion
        
        # Normalize the weights
        total_weight = sum(aspect_weights.values())
        if total_weight > 0:
            aspect_weights = {k: v/total_weight for k, v in aspect_weights.items()}
        
        # Step 6: Cross-sample by difficulty and aspect
        for difficulty in ['very easy', 'easy', 'medium', 'hard', 'very hard']:
            difficulty_quota = difficulty_quotas.get(difficulty, 0)
            if difficulty_quota <= 0:
                continue
            
            # Allocate the quota for this difficulty by aspect
            for aspect in aspects:
                aspect_quota = int(difficulty_quota * aspect_weights.get(aspect, 0.2))
                if aspect_quota == 0:
                    aspect_quota = 1  # At least select 1 (if any)
                
                key = f"{aspect}_{difficulty}"
                if key in aspect_difficulty_groups:
                    items = aspect_difficulty_groups[key]
                    take = min(aspect_quota, len(items), remaining_quota)
                    
                    if take > 0:
                        selected_from_group = self._diversify_by_file(items, take)
                        selected.extend(selected_from_group)
                        remaining_quota -= len(selected_from_group)
                        
                        if remaining_quota <= 0:
                            break
            
            if remaining_quota <= 0:
                break
        
        # Step 7: If there are remaining quotas, supplement from the groups that were not sufficiently sampled
        if remaining_quota > 0:
            remaining_by_group = {}
            for key, items in aspect_difficulty_groups.items():
                remaining_items = [item for item in items if item not in selected]
                if remaining_items:
                    remaining_by_group[key] = remaining_items
            
            if remaining_by_group:
                # Supplement by time priority
                all_remaining = []
                for items in remaining_by_group.values():
                    all_remaining.extend(items)
                all_remaining.sort(key=lambda x: x['_parsed_date'], reverse=True)
                
                selected.extend(self._diversify_by_file(all_remaining, remaining_quota))
        
        return selected[:n]
    
    def _proportional_sampling(self, n: int) -> List[Dict[str, Any]]:
        """
        Proportional sampling strategy: strictly sample according to the original proportion
        """
        # Group by formalization_aspect
        aspect_groups = defaultdict(list)
        for item in self.data:
            aspect = item['metadata']['formalization_aspect']
            aspect_groups[aspect].append(item)
        
        # Sort by time
        for aspect in aspect_groups:
            aspect_groups[aspect].sort(
                key=lambda x: x['_parsed_date'], 
                reverse=True
            )
        
        # Allocate proportionally
        selected = []
        total = len(self.data)
        
        for aspect, items in aspect_groups.items():
            proportion = len(items) / total
            take = max(1, int(n * proportion))  # At least select 1
            take = min(take, len(items))
            
            selected_from_aspect = self._diversify_by_file(items, take)
            selected.extend(selected_from_aspect)
        
        # If not enough, supplement randomly
        if len(selected) < n:
            remaining = [item for item in self.data if item not in selected]
            remaining.sort(key=lambda x: x['_parsed_date'], reverse=True)
            selected.extend(remaining[:n - len(selected)])
        
        return selected[:n]
    
    def _difficulty_focused_sampling(self, n: int) -> List[Dict[str, Any]]:
        """
        Difficulty focused strategy: ensure the difficulty distribution is more uniform
        """
        # Group by difficulty
        difficulty_groups = defaultdict(list)
        for item in self.data:
            difficulty = item['metadata']['difficulty']
            difficulty_groups[difficulty].append(item)
        
        # Sort by time
        for difficulty in difficulty_groups:
            difficulty_groups[difficulty].sort(
                key=lambda x: x['_parsed_date'], 
                reverse=True
            )
        
        # Difficulty priority: hard > medium > easy > very hard/very easy
        selected = []
        remaining_quota = n
        
        # First allocate hard
        if 'hard' in difficulty_groups:
            items = difficulty_groups['hard']
            take = min(len(items), max(5, int(n * 0.1)))  # At least 5 or 10%
            selected.extend(self._diversify_by_file(items, take))
            remaining_quota -= take
        
        # Then allocate medium
        if 'medium' in difficulty_groups and remaining_quota > 0:
            items = difficulty_groups['medium']
            take = min(len(items), max(remaining_quota // 2, int(n * 0.4)))
            selected.extend(self._diversify_by_file(items, take))
            remaining_quota -= take
        
        # Finally allocate easy
        if 'easy' in difficulty_groups and remaining_quota > 0:
            items = difficulty_groups['easy']
            selected.extend(self._diversify_by_file(items, remaining_quota))
        
        return selected[:n]
    
    def _diversify_by_file(self, items: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
        """
        File diversification strategy: avoid excessive concentration of modifications in the same file
        
        Args:
            items: Candidate list (sorted by time in reverse chronological order)
            n: Number of items to select
        
        Returns:
            Diversified selection
        """
        if n >= len(items):
            return items
        
        # Count the number of occurrences of each file
        file_counts = Counter(item['filename'] for item in items)
        
        # If all files only appear once, directly select the first n
        if all(count == 1 for count in file_counts.values()):
            return items[:n]
        
        # Otherwise, use a greedy strategy: prioritize selecting files with fewer occurrences
        selected = []
        file_selected_counts = defaultdict(int)
        max_per_file = max(2, n // len(file_counts))  # Maximum number of files to select per file
        
        for item in items:
            filename = item['filename']
            if file_selected_counts[filename] < max_per_file:
                selected.append(item)
                file_selected_counts[filename] += 1
                if len(selected) >= n:
                    break
        
        # If not enough, supplement from the remaining (by time priority)
        if len(selected) < n:
            remaining = [item for item in items if item not in selected]
            selected.extend(remaining[:n - len(selected)])
        
        return selected
    
    def analyze_sample(self, sample: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the distribution of the sampled results
        
        Args:
            sample: Sampled data
        
        Returns:
            Statistics information dictionary
        """
        stats = {
            'total': len(sample),
            'category': Counter(item['metadata']['task_category'] for item in sample),
            'aspect': Counter(item['metadata']['formalization_aspect'] for item in sample),
            'difficulty': Counter(item['metadata']['difficulty'] for item in sample),
            'change_type': Counter(item['metadata']['change_type'] for item in sample),
            'unique_files': len(set(item['filename'] for item in sample)),
            'unique_commits': len(set(item['commit_hash'] for item in sample)),
            'date_range': {
                'earliest': min(item['_parsed_date'] for item in sample).isoformat(),
                'latest': max(item['_parsed_date'] for item in sample).isoformat()
            },
            'avg_diff_lines': sum(item['metadata']['diff_lines'] for item in sample) / len(sample)
        }
        
        return stats


def split_dataset(
    data: List[Dict[str, Any]],
    test_size: int,
    strategy: str = 'balanced'
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split dataset into train and test sets

    Args:
        data: Complete dataset
        test_size: Number of samples for test set
        strategy: Sampling strategy for test set

    Returns:
        Tuple of (test_data, train_data)
    """
    splitter = StratifiedSplitter(data)
    test_data, train_data = splitter.split(test_size, strategy=strategy)

    # Clean temporary fields
    for item in test_data + train_data:
        if '_parsed_date' in item:
            del item['_parsed_date']

    return test_data, train_data

