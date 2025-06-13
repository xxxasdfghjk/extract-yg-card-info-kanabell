#!/usr/bin/env python3
import re
import json
import os
import sys
from typing import List, Optional
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict

# Constants
OUTPUT_DIR = "./output"
IMAGE_DIR = "./image"


@dataclass
class BaseCard:
    card_name: str
    card_type: str
    text: str
    image: str


@dataclass
class TrapCard(BaseCard):
    trap_type: str
    

@dataclass
class MagicCard(BaseCard):
    magic_type: str


@dataclass
class MonsterCard(BaseCard):
    monster_type: str
    level: Optional[int]
    element: str
    race: str
    attack: int
    defense: Optional[int]
    hasDefense: bool
    hasLevel: bool
    hasRank: bool
    hasLink: bool
    canNormalSummon: bool


@dataclass
class XyzMonsterCard(MonsterCard):
    rank: int
    filterAvailableMaterials: str = "() => true"
    materialCondition: str = "() => true"
    
    def __post_init__(self):
        self.hasLevel = False
        self.hasRank = True
        self.level = None


@dataclass
class FusionMonsterCard(MonsterCard):
    filterAvailableMaterials: str = "() => true"
    materialCondition: str = "() => true"


@dataclass
class SynchroMonsterCard(MonsterCard):
    filterAvailableMaterials: str = "() => true"
    materialCondition: str = "() => true"


@dataclass
class LinkMonsterCard(BaseCard):
    monster_type: str
    link: int
    linkDirection: List[str]
    element: str
    race: str
    attack: int
    hasDefense: bool = False
    hasLevel: bool = False
    hasRank: bool = False
    hasLink: bool = True
    canNormalSummon: bool = False
    filterAvailableMaterials: str = "() => true"
    materialCondition: str = "() => true"


class YugiohCardScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def read_urls_from_file(self, file_path: str) -> List[str]:
        """Read URLs from a text file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    
    def fetch_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a page."""
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    
    def determine_card_type(self, soup: BeautifulSoup) -> str:
        """Determine the type of card from the page."""
        # Look for card description box
        desc_box = soup.find('div', class_='cardDescription')
        if not desc_box:
            return "unknown"
        
        text = desc_box.get_text()
        
        # Check for card types - order matters! Check more specific types first
        if "通常罠" in text or "永続罠" in text or "カウンター罠" in text:
            return "trap"
        elif "通常魔法" in text or "永続魔法" in text or "速攻魔法" in text or "装備魔法" in text or "フィールド魔法" in text or "儀式魔法" in text:
            return "magic"
        elif "リンクモンスター" in text:
            return "link"
        elif "エクシーズモンスター" in text or "Ｘモンスター" in text:
            return "xyz"
        elif "シンクロモンスター" in text:
            return "synchro"
        elif "融合モンスター" in text:
            return "fusion"
        elif "通常モンスター" in text or "効果モンスター" in text:
            return "monster"
        
        return "unknown"
    
    def extract_card_name(self, soup: BeautifulSoup) -> str:
        """Extract card name from page."""
        # Try to get from JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict) and 'name' in data:
                    return data['name']
            except:
                pass
        
        # Try to get from image alt
        img = soup.find('img', id='detail_def_img')
        if img and img.get('alt'):
            return img['alt']
        
        return ""
    
    def extract_image_info(self, soup: BeautifulSoup) -> tuple[str, str]:
        """Extract image URL and filename."""
        img = soup.find('img', id='detail_def_img')
        if img and img.get('src'):
            img_url = img['src']
            if not img_url.startswith('http'):
                img_url = urljoin('https://www.ka-nabell.com', img_url)
            filename = os.path.basename(urlparse(img_url).path)
            return img_url, filename
        return "", ""
    
    def extract_card_text(self, soup: BeautifulSoup) -> str:
        """Extract card text."""
        desc_box = soup.find('div', class_='cardDescription')
        if desc_box:
            # Get the raw HTML content
            html_content = str(desc_box)
            
            # Remove excessive whitespace while preserving structure
            html_content = re.sub(r'\s+', ' ', html_content)
            
            # Parse again with cleaned HTML
            clean_soup = BeautifulSoup(html_content, 'html.parser')
            p_tag = clean_soup.find('p')
            
            if p_tag:
                # Replace br tags with newlines
                for br in p_tag.find_all("br"):
                    br.replace_with("\n")
                
                text = p_tag.get_text()
                
                # Split by newlines and process
                parts = text.split('\n')
                card_text_parts = []
                found_card_type = False
                
                for part in parts:
                    part = part.strip()
                    
                    # Skip empty parts
                    if not part:
                        continue
                    
                    # Skip card type (【...】)
                    if '【' in part and '】' in part:
                        found_card_type = True
                        continue
                    
                    # Skip stats line
                    if re.search(r'星\s*\d+\s*/\s*\S+\s*/\s*\S+族\s*/\s*攻\d+', part):
                        found_card_type = True
                        continue
                    
                    # Skip restriction markers
                    if part == '(制限カード)':
                        continue
                    
                    # If we found card type/stats, the rest is card text
                    if found_card_type and part:
                        card_text_parts.append(part)
                
                return ' '.join(card_text_parts)
        return ""
    
    def extract_trap_card(self, soup: BeautifulSoup) -> TrapCard:
        """Extract trap card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        
        # Determine trap type
        desc_box = soup.find('div', class_='cardDescription')
        trap_type = "通常罠"  # default
        if desc_box:
            desc_text = desc_box.get_text()
            if "永続罠" in desc_text:
                trap_type = "永続罠"
            elif "カウンター罠" in desc_text:
                trap_type = "カウンター罠"
        
        return TrapCard(
            card_name=card_name,
            card_type="罠",
            trap_type=trap_type,
            text=text,
            image=img_filename
        )
    
    def extract_magic_card(self, soup: BeautifulSoup) -> MagicCard:
        """Extract magic card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        
        # Determine magic type
        desc_box = soup.find('div', class_='cardDescription')
        magic_type = "通常魔法"  # default
        if desc_box:
            desc_text = desc_box.get_text()
            if "永続魔法" in desc_text:
                magic_type = "永続魔法"
            elif "速攻魔法" in desc_text:
                magic_type = "速攻魔法"
            elif "装備魔法" in desc_text:
                magic_type = "装備魔法"
            elif "フィールド魔法" in desc_text:
                magic_type = "フィールド魔法"
            elif "儀式魔法" in desc_text:
                magic_type = "儀式魔法"
        
        return MagicCard(
            card_name=card_name,
            card_type="魔法",
            magic_type=magic_type,
            text=text,
            image=img_filename
        )
    
    def extract_monster_stats(self, soup: BeautifulSoup) -> dict:
        """Extract monster statistics like ATK, DEF, Level, etc."""
        stats = {}
        
        desc_box = soup.find('div', class_='cardDescription')
        if desc_box:
            text = desc_box.get_text()
            
            # Look for the stats line pattern: 星 X / 属性 / 種族 / 攻XXX / 守XXX
            stats_line_match = re.search(r'星\s*(\d+)\s*/\s*(\S+)\s*/\s*(\S+族)\s*/\s*攻(\d+)\s*/\s*守(\d+)', text)
            if stats_line_match:
                stats['level'] = int(stats_line_match.group(1))
                stats['element'] = stats_line_match.group(2)
                stats['race'] = stats_line_match.group(3)
                stats['attack'] = int(stats_line_match.group(4))
                stats['defense'] = int(stats_line_match.group(5))
                stats['hasDefense'] = True
                stats['hasLevel'] = True
            else:
                # Try Link monster pattern (no defense)
                stats_line_match = re.search(r'(\S+)\s*/\s*(\S+族)\s*/\s*攻(\d+)', text)
                if stats_line_match:
                    stats['element'] = stats_line_match.group(1)
                    stats['race'] = stats_line_match.group(2)
                    stats['attack'] = int(stats_line_match.group(3))
                    stats['hasDefense'] = False
                
                # Check for Link value
                link_match = re.search(r'LINK-(\d+)', text)
                if link_match:
                    stats['link'] = int(link_match.group(1))
                    stats['hasLink'] = True
                    stats['hasLevel'] = False
                
                # Check for Rank (Xyz)
                rank_match = re.search(r'ランク\s*(\d+)', text)
                if rank_match:
                    stats['rank'] = int(rank_match.group(1))
                    stats['hasRank'] = True
                    stats['hasLevel'] = False
            
            # Determine monster type
            if "通常モンスター" in text:
                stats['monster_type'] = "通常モンスター"
            elif "効果モンスター" in text:
                stats['monster_type'] = "効果モンスター"
            elif "融合モンスター" in text:
                stats['monster_type'] = "融合モンスター"
            elif "シンクロモンスター" in text:
                stats['monster_type'] = "シンクロモンスター"
            elif "エクシーズモンスター" in text:
                stats['monster_type'] = "エクシーズモンスター"
            elif "リンクモンスター" in text:
                stats['monster_type'] = "リンクモンスター"
            
            # Extract link directions if it's a link monster
            if stats.get('hasLink') or "リンクモンスター" in text:
                # Look for LINK pattern with directions
                link_pattern = re.search(r'【LINK-\d+[：:](.*?)】', text)
                if link_pattern:
                    dirs_text = link_pattern.group(1)
                    link_dirs = []
                    # Parse the directions from the pattern
                    direction_parts = dirs_text.split('/')
                    for part in direction_parts:
                        part = part.strip()
                        if part:
                            link_dirs.append(part)
                    stats['linkDirection'] = link_dirs
                else:
                    # Fallback to arrow pattern
                    link_dirs = []
                    if "↖" in text or "左上" in text: link_dirs.append("左上")
                    if "↑" in text or "上" in text: link_dirs.append("上")
                    if "↗" in text or "右上" in text: link_dirs.append("右上")
                    if "←" in text or "左" in text: link_dirs.append("左")
                    if "→" in text or "右" in text: link_dirs.append("右")
                    if "↙" in text or "左下" in text: link_dirs.append("左下")
                    if "↓" in text or "下" in text: link_dirs.append("下")
                    if "↘" in text or "右下" in text: link_dirs.append("右下")
                    if link_dirs:
                        stats['linkDirection'] = link_dirs
            
        return stats
    
    def extract_monster_card(self, soup: BeautifulSoup) -> MonsterCard:
        """Extract normal/effect monster card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        stats = self.extract_monster_stats(soup)
        
        return MonsterCard(
            card_name=card_name,
            card_type="モンスター",
            monster_type=stats.get('monster_type', '効果モンスター'),
            level=stats.get('level'),
            element=stats.get('element', ''),
            race=stats.get('race', ''),
            attack=stats.get('attack', 0),
            defense=stats.get('defense'),
            text=text,
            image=img_filename,
            hasDefense=stats.get('hasDefense', True),
            hasLevel=stats.get('hasLevel', True),
            hasRank=False,
            hasLink=False,
            canNormalSummon=True if stats.get('monster_type') == '通常モンスター' else False
        )
    
    def extract_xyz_card(self, soup: BeautifulSoup) -> XyzMonsterCard:
        """Extract Xyz monster card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        stats = self.extract_monster_stats(soup)
        
        return XyzMonsterCard(
            card_name=card_name,
            card_type="モンスター",
            monster_type="エクシーズモンスター",
            rank=stats.get('rank', stats.get('level', 0)),
            element=stats.get('element', ''),
            race=stats.get('race', ''),
            attack=stats.get('attack', 0),
            defense=stats.get('defense', 0),
            text=text,
            image=img_filename,
            hasDefense=True,
            canNormalSummon=False
        )
    
    def extract_fusion_card(self, soup: BeautifulSoup) -> FusionMonsterCard:
        """Extract Fusion monster card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        stats = self.extract_monster_stats(soup)
        
        return FusionMonsterCard(
            card_name=card_name,
            card_type="モンスター",
            monster_type="融合モンスター",
            level=stats.get('level'),
            element=stats.get('element', ''),
            race=stats.get('race', ''),
            attack=stats.get('attack', 0),
            defense=stats.get('defense', 0),
            text=text,
            image=img_filename,
            hasDefense=True,
            hasLevel=True,
            hasRank=False,
            hasLink=False,
            canNormalSummon=False
        )
    
    def extract_synchro_card(self, soup: BeautifulSoup) -> SynchroMonsterCard:
        """Extract Synchro monster card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        stats = self.extract_monster_stats(soup)
        
        return SynchroMonsterCard(
            card_name=card_name,
            card_type="モンスター",
            monster_type="シンクロモンスター",
            level=stats.get('level'),
            element=stats.get('element', ''),
            race=stats.get('race', ''),
            attack=stats.get('attack', 0),
            defense=stats.get('defense', 0),
            text=text,
            image=img_filename,
            hasDefense=True,
            hasLevel=True,
            hasRank=False,
            hasLink=False,
            canNormalSummon=False
        )
    
    def extract_link_card(self, soup: BeautifulSoup) -> LinkMonsterCard:
        """Extract Link monster card information."""
        card_name = self.extract_card_name(soup)
        _, img_filename = self.extract_image_info(soup)
        text = self.extract_card_text(soup)
        stats = self.extract_monster_stats(soup)
        
        return LinkMonsterCard(
            card_name=card_name,
            card_type="モンスター",
            monster_type="リンクモンスター",
            link=stats.get('link', 0),
            linkDirection=stats.get('linkDirection', []),
            element=stats.get('element', ''),
            race=stats.get('race', ''),
            attack=stats.get('attack', 0),
            text=text,
            image=img_filename,
            canNormalSummon=False
        )
    
    def download_image(self, img_url: str, filename: str):
        """Download image to the image directory."""
        if not img_url:
            return
        
        try:
            response = self.session.get(img_url)
            response.raise_for_status()
            
            filepath = os.path.join(IMAGE_DIR, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
        except Exception as e:
            print(f"Failed to download image: {e}")
    
    def save_to_typescript(self, card: BaseCard, filename: str):
        """Save card data to TypeScript file."""
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Convert to dict and handle special fields
        data = asdict(card)
        
        # Create TypeScript content
        ts_content = "export default {\n"
        
        for key, value in data.items():
            if key in ['filterAvailableMaterials', 'materialCondition']:
                # These are functions, output as-is
                ts_content += f'    {key}: {value},\n'
            elif isinstance(value, str):
                if key == 'card_type' or key == 'trap_type' or key == 'magic_type' or key == 'element' or key == 'race':
                    ts_content += f'    {key}: "{value}" as const,\n'
                else:
                    ts_content += f'    {key}: "{value}",\n'
            elif isinstance(value, bool):
                ts_content += f'    {key}: {str(value).lower()} as const,\n'
            elif isinstance(value, list):
                # For linkDirection
                items = ', '.join([f'"{item}"' for item in value])
                ts_content += f'    {key}: [{items}] as const,\n'
            elif value is None:
                continue
            else:
                ts_content += f'    {key}: {value},\n'
        
        ts_content += "};\n"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ts_content)
        
        print(f"Saved: {filename}")
    
    def process_url(self, url: str):
        """Process a single URL."""
        print(f"\nProcessing: {url}")
        
        try:
            soup = self.fetch_page(url)
            card_type = self.determine_card_type(soup)
            
            if card_type == "unknown":
                print(f"Unable to determine card type for: {url}")
                return
            
            print(f"Card type: {card_type}")
            
            # Extract card based on type
            card = None
            if card_type == "trap":
                card = self.extract_trap_card(soup)
            elif card_type == "magic":
                card = self.extract_magic_card(soup)
            elif card_type == "monster":
                card = self.extract_monster_card(soup)
            elif card_type == "xyz":
                card = self.extract_xyz_card(soup)
            elif card_type == "fusion":
                card = self.extract_fusion_card(soup)
            elif card_type == "synchro":
                card = self.extract_synchro_card(soup)
            elif card_type == "link":
                card = self.extract_link_card(soup)
            
            if card:
                # Download image
                img_url, _ = self.extract_image_info(soup)
                if img_url and card.image:
                    self.download_image(img_url, card.image)
                
                # Save to TypeScript
                safe_name = re.sub(r'[^\w\s-]', '', card.card_name)
                safe_name = re.sub(r'[-\s]+', '_', safe_name)
                filename = f"{safe_name}.ts"
                self.save_to_typescript(card, filename)
                
        except Exception as e:
            print(f"Error processing {url}: {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <urls_file.txt>")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    
    if not os.path.exists(urls_file):
        print(f"File not found: {urls_file}")
        sys.exit(1)
    
    # Create directories if they don't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    # Initialize scraper
    scraper = YugiohCardScraper()
    
    # Read URLs
    urls = scraper.read_urls_from_file(urls_file)
    print(f"Found {len(urls)} URLs to process")
    
    # Process each URL
    for url in urls:
        scraper.process_url(url)
    
    print("\nProcessing complete!")


if __name__ == "__main__":
    main()