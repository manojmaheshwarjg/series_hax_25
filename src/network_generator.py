"""
Synthetic Network Data Generator
Creates realistic user profiles for testing and demo
"""

import random
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NetworkGenerator:
    """Generates synthetic network of users"""

    def __init__(self):
        self.first_names = [
            'Alex', 'Sarah', 'Michael', 'Emma', 'David', 'Lisa', 'James', 'Maria',
            'John', 'Jennifer', 'Robert', 'Linda', 'William', 'Patricia', 'Richard',
            'Jessica', 'Thomas', 'Nancy', 'Daniel', 'Karen', 'Matthew', 'Ashley',
            'Christopher', 'Emily', 'Andrew', 'Michelle', 'Joshua', 'Amanda', 'Ryan',
            'Melissa', 'Brian', 'Stephanie', 'Kevin', 'Rebecca', 'Jason', 'Laura',
            'Justin', 'Samantha', 'Mark', 'Rachel', 'Steven', 'Nicole', 'Eric', 'Amy'
        ]

        self.last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark',
            'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen', 'King',
            'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green', 'Adams',
            'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts'
        ]

        self.companies = [
            'Google', 'Meta', 'Amazon', 'Apple', 'Microsoft', 'Stripe', 'Netflix',
            'Airbnb', 'Uber', 'Lyft', 'Twitter', 'Snap', 'Pinterest', 'Dropbox',
            'Salesforce', 'Adobe', 'Oracle', 'IBM', 'Intel', 'Nvidia', 'Tesla',
            'SpaceX', 'Shopify', 'Atlassian', 'Slack', 'Zoom', 'Notion', 'Figma',
            'Linear', 'Vercel', 'Cloudflare', 'MongoDB', 'Redis', 'Snowflake'
        ]

        self.roles = [
            # Engineering
            'Software Engineer', 'Senior Software Engineer', 'Staff Engineer',
            'Engineering Manager', 'Backend Engineer', 'Frontend Engineer',
            'Full Stack Engineer', 'Mobile Engineer', 'DevOps Engineer',
            'ML Engineer', 'Data Engineer', 'Technical Lead', 'CTO',
            # Product & Design
            'Product Manager', 'Senior Product Manager', 'Product Designer',
            'UX Designer', 'UI Designer', 'UX Researcher', 'Design Lead',
            'Creative Director', 'Brand Designer', 'Graphic Designer',
            # Content & Media
            'Content Creator', 'Video Editor', 'Motion Graphics Designer',
            'Video Producer', 'Content Strategist', 'Social Media Manager',
            'Copywriter', 'Technical Writer', 'Content Marketing Manager',
            # Video Production
            'Cinematographer', 'Director of Photography', 'Video Director',
            'Post-Production Supervisor', 'Color Grader', 'Sound Designer',
            'Audio Engineer', 'Producer', 'Executive Producer',
            # Creative Tech
            '3D Artist', 'Animation Director', 'VFX Artist', 'Game Designer',
            'AR/VR Developer', 'Creative Technologist'
        ]

        self.skills = {
            'languages': ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust', 'C++', 'Ruby', 'PHP', 'Swift', 'Kotlin'],
            'frameworks': ['React', 'Vue', 'Angular', 'Next.js', 'Django', 'Flask', 'FastAPI', 'Express', 'Rails', 'Spring'],
            'cloud': ['AWS', 'GCP', 'Azure', 'Heroku', 'Vercel', 'Netlify'],
            'databases': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'DynamoDB', 'Cassandra'],
            'tools': ['Docker', 'Kubernetes', 'Git', 'Jenkins', 'Terraform', 'Ansible'],
            'ml': ['TensorFlow', 'PyTorch', 'scikit-learn', 'Keras', 'XGBoost'],
            'mobile': ['React Native', 'Flutter', 'iOS', 'Android'],
            'design': ['Figma', 'Sketch', 'Adobe XD', 'Photoshop', 'Illustrator', 'InDesign', 'Framer'],
            'video': ['Premiere Pro', 'Final Cut Pro', 'DaVinci Resolve', 'After Effects', 'Avid Media Composer'],
            'motion': ['After Effects', 'Cinema 4D', 'Blender', 'Motion', 'Nuke'],
            'audio': ['Pro Tools', 'Logic Pro', 'Ableton', 'Audition', 'Reaper'],
            '3d': ['Blender', 'Maya', 'Cinema 4D', 'Houdini', 'ZBrush', 'Unreal Engine', 'Unity'],
            'content': ['SEO', 'Content Strategy', 'Copywriting', 'Social Media', 'Analytics', 'WordPress']
        }

        self.interests = [
            'AI', 'machine learning', 'startups', 'open source', 'SaaS', 'fintech',
            'healthtech', 'edtech', 'web3', 'blockchain', 'crypto', 'climate tech',
            'e-commerce', 'developer tools', 'data science', 'cybersecurity',
            'mobile apps', 'gaming', 'AR/VR', 'IoT', 'robotics'
        ]

        self.locations = [
            'San Francisco', 'New York', 'Seattle', 'Austin', 'Boston', 'Los Angeles',
            'Chicago', 'Denver', 'Portland', 'Miami', 'Atlanta', 'Remote'
        ]

        self.projects = [
            'a SaaS product for team collaboration',
            'an AI-powered analytics platform',
            'a mobile app for fitness tracking',
            'a blockchain-based payment system',
            'an e-commerce platform for sustainable products',
            'a developer tool for code review',
            'a healthcare management system',
            'an educational platform for coding',
            'a fintech app for investing',
            'a social network for professionals',
            'an API for real-time data',
            'a marketplace for freelancers',
            'a CRM for small businesses',
            'a scheduling tool for teams',
            'an analytics dashboard'
        ]

    def generate_network(self, size: int = 50) -> List[Dict[str, Any]]:
        """
        Generate a network of synthetic users

        Args:
            size: Number of users to generate

        Returns:
            List of user profiles
        """
        users = []

        for i in range(size):
            user = self._generate_user(f"+1555{1000 + i:04d}")
            users.append(user)

        logger.info(f"Generated network of {len(users)} users")
        return users

    def _generate_user(self, phone: str) -> Dict[str, Any]:
        """Generate a single user profile"""
        first_name = random.choice(self.first_names)
        last_name = random.choice(self.last_names)
        name = f"{first_name} {last_name}"

        # Pick a role and related skills
        role = random.choice(self.roles)
        role_type = self._get_role_type(role)

        skills = self._generate_skills(role_type)
        interests = random.sample(self.interests, random.randint(2, 5))
        location = random.choice(self.locations)
        company = random.choice(self.companies) if random.random() < 0.8 else None

        # Generate project
        project = random.choice(self.projects) if random.random() < 0.6 else None

        # Generate availability
        last_active = datetime.utcnow() - timedelta(
            hours=random.randint(0, 72)
        )
        availability = 'active' if (datetime.utcnow() - last_active).total_seconds() < 86400 else 'inactive'

        # Generate communication style
        comm_style = random.choice(['casual', 'neutral', 'formal'])

        user = {
            'phone': phone,
            'name': name,
            'current_company': company,
            'role': role,
            'skills': skills,
            'interests': interests,
            'location': location,
            'projects': [project] if project else [],
            'availability': availability,
            'last_active': last_active.isoformat(),
            'communication_style': comm_style,
            'network': [],  # Will be populated later
            'conversation_history': [],
            'successful_intros_made': random.randint(0, 20),
            'successful_intros_received': random.randint(0, 15),
            'created_at': (datetime.utcnow() - timedelta(days=random.randint(1, 365))).isoformat(),
            'updated_at': last_active.isoformat(),
        }

        return user

    def _get_role_type(self, role: str) -> str:
        """Determine role type for skill generation"""
        role_lower = role.lower()

        if 'engineer' in role_lower or 'developer' in role_lower:
            if 'backend' in role_lower:
                return 'backend'
            elif 'frontend' in role_lower:
                return 'frontend'
            elif 'mobile' in role_lower:
                return 'mobile'
            elif 'devops' in role_lower:
                return 'devops'
            elif 'data' in role_lower or 'ml' in role_lower:
                return 'data'
            else:
                return 'fullstack'
        elif 'product' in role_lower:
            return 'product'
        elif 'designer' in role_lower or 'ux' in role_lower or 'ui' in role_lower:
            return 'design'
        elif 'video' in role_lower or 'editor' in role_lower or 'cinematographer' in role_lower or 'producer' in role_lower:
            return 'video'
        elif 'motion' in role_lower or 'animation' in role_lower or 'vfx' in role_lower:
            return 'motion'
        elif 'content' in role_lower or 'writer' in role_lower or 'copywriter' in role_lower:
            return 'content'
        elif '3d' in role_lower or 'artist' in role_lower:
            return '3d'
        else:
            return 'other'

    def _generate_skills(self, role_type: str) -> List[str]:
        """Generate realistic skills for a role type"""
        skills = []

        if role_type == 'backend':
            skills.extend(random.sample(self.skills['languages'], random.randint(2, 3)))
            skills.extend(random.sample(self.skills['frameworks'][:5], random.randint(1, 2)))
            skills.extend(random.sample(self.skills['databases'], random.randint(1, 2)))
            skills.extend(random.sample(self.skills['cloud'], random.randint(1, 2)))

        elif role_type == 'frontend':
            skills.extend(['JavaScript', 'TypeScript'])
            skills.extend(random.sample(self.skills['frameworks'][5:], random.randint(1, 2)))
            skills.extend(random.sample(['HTML', 'CSS', 'Tailwind', 'SCSS'], 2))

        elif role_type == 'fullstack':
            skills.extend(random.sample(self.skills['languages'][:3], 2))
            skills.extend(random.sample(self.skills['frameworks'], 2))
            skills.extend(random.sample(self.skills['databases'], 1))
            skills.extend(random.sample(self.skills['cloud'], 1))

        elif role_type == 'mobile':
            skills.extend(random.sample(self.skills['mobile'], random.randint(1, 2)))
            skills.extend(['Swift', 'Kotlin'] if random.random() < 0.5 else ['JavaScript'])

        elif role_type == 'devops':
            skills.extend(random.sample(self.skills['cloud'], 2))
            skills.extend(self.skills['tools'])
            skills.extend(['Python', 'Bash'])

        elif role_type == 'data':
            skills.extend(['Python', 'SQL'])
            skills.extend(random.sample(self.skills['ml'], random.randint(2, 3)))
            skills.extend(random.sample(self.skills['databases'], 1))

        elif role_type == 'product':
            skills.extend(['Product Strategy', 'User Research', 'Analytics', 'Roadmapping', 'Stakeholder Management'])

        elif role_type == 'design':
            skills.extend(['Figma', 'Sketch', 'UI/UX', 'Design Systems', 'Prototyping', 'User Research'])
        
        elif role_type == 'video':
            skills.extend(random.sample(self.skills['video'], random.randint(2, 3)))
            skills.extend(random.sample(self.skills['audio'], random.randint(1, 2)))
            skills.extend(['Storytelling', 'Color Grading'])
        
        elif role_type == 'motion':
            skills.extend(random.sample(self.skills['motion'], random.randint(2, 3)))
            skills.extend(random.sample(self.skills['3d'], random.randint(1, 2)))
        
        elif role_type == 'content':
            skills.extend(random.sample(self.skills['content'], random.randint(3, 5)))
            skills.extend(['Writing', 'Editing', 'Research'])
        
        elif role_type == '3d':
            skills.extend(random.sample(self.skills['3d'], random.randint(2, 4)))
            skills.extend(['Modeling', 'Texturing', 'Lighting', 'Rendering'])

        else:
            skills.extend(random.sample(self.skills['languages'], 2))

        return list(set(skills))  # Remove duplicates

    def add_network_connections(self, users: List[Dict[str, Any]], avg_connections: int = 10):
        """
        Add network connections between users

        Args:
            users: List of user profiles
            avg_connections: Average number of connections per user
        """
        for user in users:
            # Generate connections based on:
            # - Same location (higher probability)
            # - Similar skills/interests
            # - Same company

            potential_connections = [
                u for u in users
                if u['phone'] != user['phone']
            ]

            # Calculate connection probabilities
            connections = []
            for potential in potential_connections:
                prob = self._calculate_connection_probability(user, potential)

                if random.random() < prob:
                    connections.append(potential['phone'])

                if len(connections) >= avg_connections * 2:
                    break

            # Randomly sample to get to avg
            if len(connections) > avg_connections:
                connections = random.sample(connections, avg_connections)

            user['network'] = connections

        logger.info(f"Added network connections (avg {avg_connections} per user)")

    def _calculate_connection_probability(self, user1: Dict, user2: Dict) -> float:
        """Calculate probability of connection between two users"""
        prob = 0.1  # Base probability

        # Same company
        if user1.get('current_company') == user2.get('current_company') and user1.get('current_company'):
            prob += 0.4

        # Same location
        if user1.get('location') == user2.get('location'):
            prob += 0.2

        # Similar interests
        common_interests = set(user1.get('interests', [])) & set(user2.get('interests', []))
        if common_interests:
            prob += 0.1 * len(common_interests)

        # Similar skills
        common_skills = set(user1.get('skills', [])) & set(user2.get('skills', []))
        if common_skills:
            prob += 0.05 * len(common_skills)

        return min(prob, 0.9)  # Cap at 90%


if __name__ == "__main__":
    # Test network generation
    logging.basicConfig(level=logging.INFO)

    generator = NetworkGenerator()

    # Generate 20 users
    users = generator.generate_network(20)

    print(f"\nGenerated {len(users)} users\n")

    # Show sample users
    for i, user in enumerate(users[:3]):
        print(f"\nUser {i+1}: {user['name']}")
        print(f"  Role: {user['role']}")
        print(f"  Company: {user.get('current_company', 'N/A')}")
        print(f"  Location: {user['location']}")
        print(f"  Skills: {', '.join(user['skills'][:5])}")
        print(f"  Interests: {', '.join(user['interests'][:3])}")
        print(f"  Phone: {user['phone']}")

    # Add connections
    generator.add_network_connections(users, avg_connections=8)

    print(f"\nNetwork connections added")
    print(f"User 1 has {len(users[0]['network'])} connections")
    print(f"User 2 has {len(users[1]['network'])} connections")
