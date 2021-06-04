// Copyright 2018-2021 - John snow wind

#include "AutoPSDUISetting.h"

UAutoPSDUISetting::UAutoPSDUISetting()
{
	this->CategoryName = TEXT("Plugins");
	bEnabled = true;
	TextureSrcDir.Path =  FPaths::ProjectDir() / TEXT("Art/UI/Texture");
	TextureAssetDir.Path = TEXT("/Game/Widgets/Texture");
}

UAutoPSDUISetting* UAutoPSDUISetting::Get()
{
	return Cast<UAutoPSDUISetting>(StaticClass()->GetDefaultObject());
}
