from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.services.user_profile_service import UserProfileService
from app.services.user_behavior_service import UserBehaviorService
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate, UserPreferenceProfile, UserSegment
from app.models.user_behavior import UserBehavior

router = APIRouter(prefix="/api/user-profiles", tags=["user-profiles"])


@router.post("/", response_model=UserProfile)
def create_user_profile(
    profile_data: UserProfileCreate,
    profile_service: UserProfileService = Depends(UserProfileService)
):
    """创建用户画像"""
    try:
        profile = profile_service.create_profile(profile_data)
        return profile
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}", response_model=Optional[UserProfile])
def get_user_profile(
    user_id: str,
    profile_type: Optional[str] = None,
    profile_service: UserProfileService = Depends(UserProfileService)
):
    """获取用户画像"""
    try:
        profile = profile_service.get_profile(user_id, profile_type)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}", response_model=Optional[UserProfile])
def update_user_profile(
    user_id: str,
    profile_update: UserProfileUpdate,
    profile_service: UserProfileService = Depends(UserProfileService)
):
    """更新用户画像"""
    try:
        updated_profile = profile_service.update_profile(user_id, profile_update)
        if not updated_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return updated_profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{user_id}/preference", response_model=UserPreferenceProfile)
def build_preference_profile(
    user_id: str,
    profile_service: UserProfileService = Depends(UserProfileService),
    behavior_service: UserBehaviorService = Depends(UserBehaviorService)
):
    """基于用户行为构建偏好画像"""
    try:
        # 获取用户行为数据
        behaviors = behavior_service.get_user_behaviors(user_id)
        
        # 构建用户偏好画像
        profile = profile_service.build_preference_profile(user_id, behaviors)
        return profile
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/segment", response_model=List[UserSegment])
def segment_users(
    user_ids: List[str],
    profile_service: UserProfileService = Depends(UserProfileService)
):
    """用户分群"""
    try:
        # 获取用户画像
        profiles = []
        for user_id in user_ids:
            profile = profile_service.get_profile(user_id)
            if profile:
                profiles.append(profile)
        
        # 执行分群
        segments = profile_service.segment_users(profiles)
        return segments
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-update")
def batch_update_profiles(
    profiles_data: List[dict],
    profile_service: UserProfileService = Depends(UserProfileService)
):
    """批量更新用户画像"""
    try:
        updated_count = profile_service.update_profile_batch(profiles_data)
        return {"updated_count": updated_count}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
